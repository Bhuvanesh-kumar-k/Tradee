from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_verified_user
from app.models.user import User
from app.schemas.scanner import SingleCoinCheckRequest, CoinAnalysisResult, ScannerLogResponse
from app.core.strategy import evaluate_pair, evaluate_all_markets, get_market_trend
from app.core.news_calendar import circuit_breaker
from app.models.scanner_log import ScannerLog
from app.services.coindcx_executor import CoinDCXExecutor
from sqlalchemy import select
from datetime import datetime
import httpx

router = APIRouter(prefix="/scanner", tags=["Market Scanner"])


async def convert_to_usdt(amount: float, preferred_currency: str) -> float:
    """Convert amount to USDT based on preferred currency"""
    if preferred_currency == "INR":
        return amount / 90.0  # Approximate conversion rate
    return amount


@router.get("/status")
async def get_scanner_status(
    current_user: User = Depends(get_current_user)
):
    """Get current scanner status including news circuit breaker"""
    frozen_status = circuit_breaker.get_frozen_status_message()
    upcoming_events = circuit_breaker.get_upcoming_events(hours=24)
    
    return {
        "status": "frozen" if frozen_status else "active",
        "message": frozen_status or "Scanner running normally",
        "upcoming_events": upcoming_events,
        "scan_interval_minutes": current_user.scan_interval_minutes
    }


@router.post("/check-coin", response_model=CoinAnalysisResult)
async def check_single_coin(
    request: SingleCoinCheckRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Run on-demand analysis for a single coin"""
    # Check circuit breaker
    frozen_status = circuit_breaker.get_frozen_status_message()
    if frozen_status:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Scanner frozen: {frozen_status}"
        )
    
    # Normalize coin pair
    coin_pair = request.coin_pair.upper()
    if not coin_pair.startswith("B-"):
        coin_pair = f"B-{coin_pair}"
    if not coin_pair.endswith("_USDT"):
        coin_pair = f"{coin_pair}_USDT"
    
    # Get BTC trend
    btc_trend = await get_market_trend("B-BTC_USDT", "1d")
    
    # Determine capital allocation
    capital = current_user.custom_margin_allocation
    if capital is None:
        # Fetch live balance from CoinDCX using ephemeral headers
        if x_coindcx_key and x_coindcx_secret:
            executor = CoinDCXExecutor(x_coindcx_key, x_coindcx_secret)
            balance_data = await executor.get_futures_balance()
            if balance_data:
                total_balance = 0.0
                if isinstance(balance_data, list):
                    for item in balance_data:
                        if isinstance(item, dict) and item.get("currency") in ["USDT", "USDT_FUTURES"]:
                            total_balance = float(item.get("balance", 0.0))
                            break
                elif isinstance(balance_data, dict):
                    total_balance = float(balance_data.get("balance", 0) or balance_data.get("total_balance", 0) or balance_data.get("usdt_balance", 0) or 0.0)
                
                if total_balance > 0:
                    risk_pct = getattr(current_user, "risk_percentage_per_trade", 0.25)
                    capital = total_balance * risk_pct
        
        # Fallback if balance fetch failed or no keys
        if capital is None or capital < 20:
            capital = 20.0  # Minimum fallback
    
    # Convert capital to USDT if user prefers INR
    capital = await convert_to_usdt(capital, current_user.preferred_currency)
    
    # Get user's selected timeframes, fallback to defaults if empty
    user_timeframes = current_user.trading_timeframes if current_user.trading_timeframes else ["1h", "4h", "8h", "1d"]
    
    # Evaluate the coin with user-selected timeframes
    trades = await evaluate_pair(
        coin_pair,
        capital=capital,
        btc_trend=btc_trend,
        user_timeframes=user_timeframes
    )
    
    if not trades:
        return CoinAnalysisResult(
            coin_pair=coin_pair,
            timeframes=[],
            overall_signal="NONE",
            best_timeframe=None,
            entry_price=None,
            take_profit=None,
            stop_loss=None,
            leverage=None,
            expected_roi=None
        )
    
    best_trade = max(trades, key=lambda x: x["roi_num"])
    
    # Log the scan
    log = ScannerLog(
        user_id=current_user.id,
        coin_pair=coin_pair,
        timeframe=best_trade["Timeframe"],
        trend_status="BULLISH" if best_trade["Direction"] == "LONG" else "BEARISH",
        signal_detected=best_trade["Direction"],
        checklist_passed=best_trade.get("checklist"),
        **best_trade.get("indicator_values", {})
    )
    db.add(log)
    await db.commit()
    
    return CoinAnalysisResult(
        coin_pair=coin_pair,
        timeframes=[
            {
                "timeframe": t["Timeframe"],
                "direction": t["Direction"],
                "roi": t["roi_num"],
                "entry": t["Entry Price"],
                "tp": t["Take Profit"],
                "sl": t["Stop Loss"]
            }
            for t in trades
        ],
        overall_signal=best_trade["Direction"],
        best_timeframe=best_trade["Timeframe"],
        entry_price=best_trade["Entry Price"],
        take_profit=best_trade["Take Profit"],
        stop_loss=best_trade["Stop Loss"],
        leverage=best_trade["Leverage"],
        expected_roi=best_trade["roi_num"]
    )


@router.get("/logs", response_model=list[ScannerLogResponse])
async def get_scanner_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent scanner logs"""
    result = await db.execute(
        select(ScannerLog)
        .where(ScannerLog.user_id == current_user.id)
        .order_by(ScannerLog.scan_time.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [ScannerLogResponse.model_validate(log) for log in logs]


@router.get("/balance")
async def get_live_balance(
    current_user: User = Depends(get_current_verified_user),
    x_coindcx_key: str = Header(None, alias="XCoinDCXKey"),
    x_coindcx_secret: str = Header(None, alias="XCoinDCXSecret"),
):
    """Fetch live CoinDCX balance using client-side ephemeral headers"""
    if not x_coindcx_key or not x_coindcx_secret:
        return {"balance": 0.0, "margin_in_use": 0.0, "currency": "USDT"}
        
    executor = CoinDCXExecutor(x_coindcx_key, x_coindcx_secret)
    balance_data = await executor.get_futures_balance()
    
    total_balance = 0.0
    if isinstance(balance_data, list):
        for item in balance_data:
            if isinstance(item, dict) and item.get("currency") in ["USDT", "USDT_FUTURES"]:
                total_balance = float(item.get("balance", 0.0))
                break
    elif isinstance(balance_data, dict):
        total_balance = float(balance_data.get("balance", 0) or balance_data.get("total_balance", 0) or balance_data.get("usdt_balance", 0) or 0.0)
        
    return {
        "balance": total_balance,
        "margin_in_use": 0.0,
        "currency": "USDT"
    }
