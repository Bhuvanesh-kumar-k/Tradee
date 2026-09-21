from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_verified_user
from app.models.user import User
from app.schemas.scanner import (
    SingleCoinCheckRequest,
    CoinAnalysisResult,
    ScannerLogResponse,
    TimeframeCheckDetail
)
from app.core.strategy import evaluate_pair, evaluate_all_markets, get_market_trend, get_btc_macro_trend, evaluate_pair_diagnostics
from app.core.news_calendar import circuit_breaker
from app.models.scanner_log import ScannerLog
from app.services.coindcx_executor import CoinDCXExecutor
from app.services.binance_executor import BinanceExecutor
from app.core.config import settings
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
    db: AsyncSession = Depends(get_db),
    x_coindcx_key: str = Header(None, alias="XCoinDCXKey"),
    x_coindcx_secret: str = Header(None, alias="XCoinDCXSecret"),
    x_binance_key: str = Header(None, alias="XBinanceKey"),
    x_binance_secret: str = Header(None, alias="XBinanceSecret"),
):
    """Run on-demand analysis for a single coin"""
    frozen_status = circuit_breaker.get_frozen_status_message()
    if frozen_status:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Scanner frozen: {frozen_status}")

    raw_pair = request.coin_pair.strip().upper().replace("/", "_").replace("-", "_")
    if raw_pair.startswith("B_"):
        raw_pair = raw_pair[2:]
    if not raw_pair.endswith("_USDT"):
        raw_pair = f"{raw_pair[:-4]}_USDT" if raw_pair.endswith("USDT") else f"{raw_pair}_USDT"
    coin_pair = f"B-{raw_pair}"

    btc_trend = await get_btc_macro_trend()
    capital = current_user.custom_margin_allocation or 20.0

    eval_result = await evaluate_pair_diagnostics(
        coin_pair,
        capital=capital,
        btc_trend=btc_trend,
        user_timeframes=current_user.trading_timeframes or ["4h", "8h", "1d"]
    )

    candidate_trades = eval_result["candidate_trades"]
    timeframe_details = eval_result["timeframe_details"]

    if candidate_trades:
        best_trade = max(candidate_trades, key=lambda x: x.roi or 0.0)
        summary = f"Approved {best_trade.direction} on {best_trade.timeframe}. Confluence confirmed."
        overall_signal = best_trade.direction or "LONG"
        best_tf = best_trade.timeframe
        entry_p = best_trade.entry
        tp_p = best_trade.tp
        sl_p = best_trade.sl
        lev = best_trade.leverage
        exp_roi = best_trade.roi
    else:
        all_failed = set()
        for tf in timeframe_details:
            for fc in tf.failed_checks:
                all_failed.add(fc)
        fail_str = ", ".join(list(all_failed)[:3]) if all_failed else "Criteria not satisfied"
        summary = f"Trade Not Recommended. Unmet conditions: {fail_str}."
        overall_signal = "NEUTRAL"
        best_tf = None
        entry_p = None
        tp_p = None
        sl_p = None
        lev = None
        exp_roi = None

    log = ScannerLog(
        user_id=current_user.id,
        coin_pair=coin_pair,
        timeframe=best_tf or "1h",
        trend_status=eval_result["macro_1d_trend"],
        signal_detected=overall_signal,
        checklist_passed={"summary": summary, "failed": list(all_failed) if not candidate_trades else []}
    )
    db.add(log)
    await db.commit()

    return CoinAnalysisResult(
        coin_pair=coin_pair,
        macro_1d_trend=eval_result["macro_1d_trend"],
        ltf_1h_trend=eval_result["ltf_1h_trend"],
        btc_macro_trend=btc_trend,
        timeframes=timeframe_details,
        overall_signal=overall_signal,
        best_timeframe=best_tf,
        entry_price=entry_p,
        take_profit=tp_p,
        stop_loss=sl_p,
        leverage=lev,
        expected_roi=exp_roi,
        summary_reason=summary
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
    x_binance_key: str = Header(None, alias="XBinanceKey"),
    x_binance_secret: str = Header(None, alias="XBinanceSecret"),
    x_binance_testnet: str = Header(None, alias="XBinanceTestnet"),
):
    """Fetch live balance from Binance or CoinDCX using client-side ephemeral keys"""
    # 1. Check Binance
    if x_binance_key and x_binance_secret:
        is_testnet = str(x_binance_testnet).lower() == "true"
        executor = BinanceExecutor(x_binance_key, x_binance_secret, testnet=is_testnet)
        bal = await executor.get_futures_balance()
        return {"balance": bal, "margin_in_use": 0.0, "currency": "USDT", "exchange": "Binance"}

    # 2. Check CoinDCX
    if x_coindcx_key and x_coindcx_secret:
        executor = CoinDCXExecutor(x_coindcx_key, x_coindcx_secret)
        balance_data = await executor.get_futures_balance()
        total_balance = 0.0
        if isinstance(balance_data, list):
            for item in balance_data:
                if isinstance(item, dict) and item.get("currency") in ["USDT", "USDT_FUTURES"]:
                    total_balance = float(item.get("balance", 0.0))
                    break
        elif isinstance(balance_data, dict):
            total_balance = float(balance_data.get("balance", 0) or balance_data.get("total_balance", 0) or 0.0)
        return {"balance": total_balance, "margin_in_use": 0.0, "currency": "USDT", "exchange": "CoinDCX"}

    return {"balance": 0.0, "margin_in_use": 0.0, "currency": "USDT", "exchange": "None"}


@router.get("/scan-all")
async def scan_all_default_coins(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    btc_trend = await get_btc_macro_trend()
    capital = current_user.custom_margin_allocation or 20.0
    coins_to_scan = settings.DEFAULT_COINS
    results = []

    for coin in coins_to_scan:
        diag = await evaluate_pair_diagnostics(
            coin,
            capital=capital,
            btc_trend=btc_trend,
            user_timeframes=current_user.trading_timeframes or ["4h", "8h", "1d"]
        )
        
        has_approved = len(diag["candidate_trades"]) > 0
        best_setup = diag["candidate_trades"][0] if has_approved else None
        
        results.append({
            "coin_pair": diag["coin_pair"],
            "1d_status": diag["macro_1d_trend"],
            "1h_status": diag["ltf_1h_trend"],
            "has_approved": has_approved,
            "best_direction": best_setup.direction if best_setup else "NEUTRAL",
            "best_timeframe": best_setup.timeframe if best_setup else None,
            "timeframes": [tf.model_dump() for tf in diag["timeframe_details"]]
        })

    return {
        "btc_macro_trend": btc_trend,
        "scanned_at": datetime.utcnow().isoformat(),
        "coins": results
    }
