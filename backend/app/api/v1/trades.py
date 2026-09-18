from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_verified_user
from app.models.user import User
from app.models.trade import Trade
from app.schemas.trade import TradeResponse, ManualCloseRequest, TradeStats
from app.services.position_tracker import PositionTracker
from app.services.coindcx_executor import get_user_executor
from app.core.news_calendar import circuit_breaker

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("/active", response_model=list[TradeResponse])
async def get_active_trades(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active positions for current user"""
    trades = await PositionTracker.get_active_positions(db, current_user.id)
    return [TradeResponse.model_validate(trade) for trade in trades]


@router.get("/history", response_model=list[TradeResponse])
async def get_trade_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trade history for current user"""
    result = await db.execute(
        select(Trade)
        .where(Trade.user_id == current_user.id)
        .order_by(Trade.entry_time.desc())
        .limit(limit)
    )
    trades = result.scalars().all()
    return [TradeResponse.model_validate(trade) for trade in trades]


@router.get("/stats", response_model=TradeStats)
async def get_trade_statistics(
    period: str = "today",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trade statistics for a period (today, yesterday, week, month)"""
    stats = await PositionTracker.get_trade_stats(db, current_user.id, period)
    return TradeStats(**stats)


@router.post("/close")
async def close_position(
    request: ManualCloseRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually close a position"""
    # Get the trade
    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.id == request.trade_id,
                Trade.user_id == current_user.id,
                Trade.status == "OPEN"
            )
        )
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found or already closed"
        )
    
    # Execute close on CoinDCX
    executor = await get_user_executor(current_user)
    if executor:
        try:
            # Calculate quantity to close
            quantity = (trade.margin_used * trade.leverage) / trade.entry_price
            await executor.close_position(trade.coin_pair, quantity)
        except Exception as e:
            print(f"Failed to close position on exchange: {e}")
    
    # Close in database
    await PositionTracker.close_position(db, trade, None, "MANUAL")
    
    return {"message": "Position closed successfully"}


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific trade"""
    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.id == trade_id,
                Trade.user_id == current_user.id
            )
        )
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    return TradeResponse.model_validate(trade)


@router.post("/update-pnl")
async def update_all_pnl(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update PnL for all active positions (background task)"""
    async def update_task():
        trades = await PositionTracker.get_active_positions(db, current_user.id)
        for trade in trades:
            await PositionTracker.update_position_pnl(db, trade)
    
    background_tasks.add_task(update_task)
    return {"message": "PnL update started in background"}
