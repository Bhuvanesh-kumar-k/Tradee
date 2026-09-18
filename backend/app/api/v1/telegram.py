from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_verified_user
from app.models.user import User
from app.models.telegram_signal import TelegramSignal
from app.services.telegram_service import TelegramSignalListener, active_listeners
from app.services.ai_service import AIService
from app.core.strategy import get_market_trend
from app.core.market_data import fetch_raw_candles
from app.core.indicators import calculate_all_indicators
from sqlalchemy import select
from typing import List

router = APIRouter(prefix="/telegram", tags=["Telegram Signals"])


@router.post("/start")
async def start_telegram_listener(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    x_telegram_api_id: str = Header(None, alias="XTelegramApiId"),
    x_telegram_api_hash: str = Header(None, alias="XTelegramApiHash"),
):
    """Start Telegram signal listener for user"""
    if not x_telegram_api_id or not x_telegram_api_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram credentials not provided in headers"
        )
    
    if not current_user.telegram_channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Telegram channels configured"
        )
    
    if current_user.id in active_listeners:
        return {"message": "Listener already running"}
    
    # Create and start listener with user-specific session using ephemeral headers
    listener = TelegramSignalListener(
        current_user.id,
        x_telegram_api_id,
        x_telegram_api_hash,
        current_user.telegram_channels
    )
    
    # Set callback to handle signals
    async def handle_signal(signal_data):
        # Save signal to database
        signal = TelegramSignal(
            user_id=current_user.id,
            coin_pair=signal_data.get("coin_pair"),
            direction=signal_data.get("direction"),
            leverage=signal_data.get("leverage"),
            entry_zone=signal_data.get("entry_zone"),
            take_profit_targets=signal_data.get("take_profit_targets"),
            stop_loss=signal_data.get("stop_loss"),
            channel_name=signal_data.get("channel_name"),
            channel_id=signal_data.get("channel_id"),
            message_id=signal_data.get("message_id"),
            raw_message=signal_data.get("raw_message"),
            received_at=signal_data.get("timestamp")
        )
        db.add(signal)
        await db.commit()
        
        # AI Analysis if enabled - requires AI API key from headers
        # Note: AI keys are now stored client-side and passed via headers
        # This endpoint would need to accept X-AI-Key header for AI analysis
        # For now, skip AI analysis as it requires ephemeral key passing
    
    listener.set_signal_callback(handle_signal)
    
    # Start in background
    async def start_listener():
        await listener.start()
    
    background_tasks.add_task(start_listener)
    active_listeners[current_user.id] = listener
    
    return {"message": "Telegram listener started"}


@router.post("/stop")
async def stop_telegram_listener(
    current_user: User = Depends(get_current_user)
):
    """Stop Telegram signal listener for user"""
    if current_user.id not in active_listeners:
        return {"message": "Listener not running"}
    
    listener = active_listeners[current_user.id]
    await listener.stop()
    del active_listeners[current_user.id]
    
    return {"message": "Telegram listener stopped"}


@router.get("/signals")
async def get_telegram_signals(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get received Telegram signals"""
    result = await db.execute(
        select(TelegramSignal)
        .where(TelegramSignal.user_id == current_user.id)
        .order_by(TelegramSignal.received_at.desc())
        .limit(limit)
    )
    signals = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "coin_pair": s.coin_pair,
            "direction": s.direction,
            "leverage": s.leverage,
            "entry_zone": s.entry_zone,
            "take_profit_targets": s.take_profit_targets,
            "stop_loss": s.stop_loss,
            "channel_name": s.channel_name,
            "ai_verdict": s.ai_verdict,
            "ai_reasoning": s.ai_reasoning,
            "ai_confidence": s.ai_confidence,
            "received_at": s.received_at,
            "is_processed": s.is_processed
        }
        for s in signals
    ]


@router.get("/status")
async def get_telegram_status(
    current_user: User = Depends(get_current_user)
):
    """Get Telegram listener status"""
    return {
        "is_running": current_user.id in active_listeners,
        "channels": current_user.telegram_channels,
        "has_credentials": bool(current_user.telegram_api_id and current_user.telegram_api_hash)
    }
ch