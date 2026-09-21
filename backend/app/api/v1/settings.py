from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.settings import UserSettingsUpdate, AIKeyVerify
from app.models.user import User
from app.services.ai_service import AIService
from app.services.coindcx_executor import CoinDCXExecutor
import httpx

router = APIRouter(prefix="/settings", tags=["User Settings"])


@router.get("/me")
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """Get current user settings (excluding sensitive data)"""
    return {
        "email": current_user.email,
        "name": current_user.name,
        "experience_level": current_user.experience_level,
        "terms_accepted": current_user.terms_accepted,
        "custom_margin_allocation": current_user.custom_margin_allocation,
        "risk_percentage_per_trade": getattr(current_user, "risk_percentage_per_trade", 0.25),
        "scan_interval_minutes": current_user.scan_interval_minutes,
        "ai_provider": current_user.ai_provider,
        "ai_enabled": current_user.ai_enabled,
        "telegram_channels": current_user.telegram_channels or [],
        "auto_trading_enabled": current_user.auto_trading_enabled,
        "preferred_currency": current_user.preferred_currency,
        "trading_timeframes": current_user.trading_timeframes or ["1h", "4h", "8h", "1d"]
    }


@router.put("/me")
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings (keys stored client-side, not in database)"""
    if settings_update.margin:
        current_user.custom_margin_allocation = settings_update.margin.custom_margin_allocation
        if settings_update.margin.risk_percentage_per_trade is not None:
            current_user.risk_percentage_per_trade = settings_update.margin.risk_percentage_per_trade
        current_user.scan_interval_minutes = settings_update.margin.scan_interval_minutes
    
    if settings_update.ai:
        current_user.ai_provider = settings_update.ai.provider
        current_user.ai_enabled = False  # Require verification
    
    if settings_update.telegram:
        current_user.telegram_channels = settings_update.telegram.channels
    
    if settings_update.trading:
        current_user.auto_trading_enabled = settings_update.trading.auto_trading_enabled
        current_user.preferred_currency = settings_update.trading.preferred_currency
        current_user.trading_timeframes = settings_update.trading.trading_timeframes
    
    await db.commit()
    await db.refresh(current_user)
    
    return {"message": "Settings updated successfully"}


@router.post("/verify-ai-key")
async def verify_ai_key(
    verify_request: AIKeyVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify AI API key with a test prompt using structured JSON"""
    try:
        # Test with a simple signal analysis to verify the key works
        test_signal = {
            "coin_pair": "BTC_USDT",
            "direction": "LONG",
            "leverage": "10x",
            "entry_zone": "67000",
            "take_profit_targets": ["69000"],
            "stop_loss": "66000"
        }
        
        test_market_context = {
            "btc_trend": "BULLISH",
            "coin_1d_trend": "BULLISH",
            "coin_1h_trend": "BULLISH",
            "rsi": 55,
            "macd_hist": 0.5,
            "adx": 25,
            "ema50": 66500,
            "ema200": 65000
        }
        
        result = await AIService.analyze_signal(
            verify_request.provider,
            verify_request.api_key,
            test_signal,
            test_market_context
        )
        
        # Check if the result is valid
        if result.get("verdict") in ["APPROVE", "REJECT"] and result.get("confidence", 0) > 0:
            current_user.ai_provider = verify_request.provider
            # AI keys are now stored client-side, not in database
            current_user.ai_enabled = True
            await db.commit()
            return {
                "message": "AI key verified successfully",
                "provider": verify_request.provider,
                "test_result": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI key verification failed: {result.get('reason', 'Unknown error')}"
            )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI API timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI verification failed: {str(e)}"
        )


@router.post("/verify-coindcx-keys")
async def verify_coindcx_keys(
    x_coindcx_key: str = Header(None, alias="XCoinDCXKey"),
    x_coindcx_secret: str = Header(None, alias="XCoinDCXSecret"),
):
    """Verify CoinDCX API keys by fetching futures balance"""
    if not x_coindcx_key or not x_coindcx_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CoinDCX API key and secret are required"
        )
    
    try:
        executor = CoinDCXExecutor(x_coindcx_key, x_coindcx_secret)
        balance_data = await executor.get_futures_balance()
        
        if balance_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid CoinDCX API credentials"
            )
        
        # Check if balance data is valid
        if isinstance(balance_data, list):
            total_balance = 0.0
            for item in balance_data:
                if isinstance(item, dict) and item.get("currency") in ["USDT", "USDT_FUTURES"]:
                    total_balance = float(item.get("balance", 0.0))
                    break
        elif isinstance(balance_data, dict):
            total_balance = float(balance_data.get("balance", 0) or balance_data.get("total_balance", 0) or 0.0)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response format from CoinDCX API"
            )
        
        return {
            "message": "CoinDCX keys verified successfully",
            "balance": total_balance,
            "currency": "USDT"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CoinDCX verification failed: {str(e)}"
        )


@router.post("/verify-telegram-credentials")
async def verify_telegram_credentials(
    api_id: str,
    api_hash: str,
):
    """Verify Telegram API credentials by checking format"""
    if not api_id or not api_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram API ID and Hash are required"
        )
    
    try:
        # Basic format validation
        if not api_id.isdigit() or len(api_id) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Telegram API ID format"
            )
        
        if len(api_hash) < 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Telegram API Hash format"
            )
        
        # Note: Full validation would require attempting to connect to Telegram
        # For now, we validate format only
        return {
            "message": "Telegram credentials format validated successfully",
            "api_id": api_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram verification failed: {str(e)}"
        )
