from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.trade import Trade, TradeLog
from app.models.user import User
from app.core.market_data import fetch_current_price
from app.core.indicators import calculate_all_indicators
from app.core.market_data import fetch_raw_candles
import pandas as pd


class PositionTracker:
    """Track and manage active trading positions"""
    
    @staticmethod
    async def get_active_positions(db: AsyncSession, user_id: int) -> List[Trade]:
        """Get all active positions for a user"""
        result = await db.execute(
            select(Trade).where(
                and_(
                    Trade.user_id == user_id,
                    Trade.status == "OPEN"
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_position_pnl(db: AsyncSession, trade: Trade) -> Optional[float]:
        """Update PnL for a position based on current price"""
        current_price = await fetch_current_price(trade.coin_pair)
        if current_price is None:
            return None
        
        if trade.direction == "LONG":
            pnl_percentage = ((current_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
        else:  # SHORT
            pnl_percentage = ((trade.entry_price - current_price) / trade.entry_price) * 100 * trade.leverage
        
        pnl = (pnl_percentage / 100) * trade.margin_used
        trade.pnl = pnl
        trade.pnl_percentage = pnl_percentage
        
        await db.commit()
        return pnl
    
    @staticmethod
    async def check_exit_conditions(db: AsyncSession, trade: Trade) -> Optional[str]:
        """
        Check if position should be closed based on:
        - Take Profit hit
        - Stop Loss hit
        - Early exit indicators (EMA50 break, MACD turn)
        """
        current_price = await fetch_current_price(trade.coin_pair)
        if current_price is None:
            return None
        
        # Check TP
        if trade.direction == "LONG" and current_price >= trade.take_profit:
            return "TP"
        elif trade.direction == "SHORT" and current_price <= trade.take_profit:
            return "TP"
        
        # Check SL
        if trade.direction == "LONG" and current_price <= trade.stop_loss:
            return "SL"
        elif trade.direction == "SHORT" and current_price >= trade.stop_loss:
            return "SL"
        
        # Early Exit Indicators (1H timeframe)
        df_1h = await fetch_raw_candles(trade.coin_pair, interval="1h", limit=100)
        if df_1h is not None and len(df_1h) >= 50:
            df_1h = calculate_all_indicators(df_1h)
            closed_bar = df_1h.iloc[-2]
            
            if trade.direction == "LONG":
                # Check if 1H closed below EMA50
                if closed_bar["close"] < closed_bar["ema50"]:
                    return "EARLY_EXIT_EMA50"
                # Check if MACD turned negative
                if closed_bar["macdhist"] < 0:
                    return "EARLY_EXIT_MACD"
            else:  # SHORT
                # Check if 1H closed above EMA50
                if closed_bar["close"] > closed_bar["ema50"]:
                    return "EARLY_EXIT_EMA50"
                # Check if MACD turned positive
                if closed_bar["macdhist"] > 0:
                    return "EARLY_EXIT_MACD"
        
        return None
    
    @staticmethod
    async def close_position(
        db: AsyncSession,
        trade: Trade,
        exit_price: float,
        exit_reason: str
    ) -> Trade:
        """Close a position and record final PnL"""
        current_price = exit_price if exit_price else await fetch_current_price(trade.coin_pair)
        
        if current_price:
            if trade.direction == "LONG":
                pnl_percentage = ((current_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
            else:
                pnl_percentage = ((trade.entry_price - current_price) / trade.entry_price) * 100 * trade.leverage
            
            trade.pnl = (pnl_percentage / 100) * trade.margin_used
            trade.pnl_percentage = pnl_percentage
        
        trade.status = "CLOSED"
        trade.exit_price = current_price
        trade.exit_reason = exit_reason
        trade.exit_time = datetime.utcnow()
        
        # Log the exit
        log = TradeLog(
            user_id=trade.user_id,
            trade_id=trade.id,
            log_type="EXIT",
            message=f"Position closed: {exit_reason}",
            metadata={
                "exit_price": current_price,
                "pnl": trade.pnl,
                "pnl_percentage": trade.pnl_percentage
            }
        )
        db.add(log)
        
        await db.commit()
        await db.refresh(trade)
        
        return trade
    
    @staticmethod
    async def log_trade_event(
        db: AsyncSession,
        user_id: int,
        trade_id: Optional[int],
        log_type: str,
        message: str,
        metadata: Optional[dict] = None
    ):
        """Log a trade event"""
        log = TradeLog(
            user_id=user_id,
            trade_id=trade_id,
            log_type=log_type,
            message=message,
            metadata=metadata
        )
        db.add(log)
        await db.commit()
    
    @staticmethod
    async def get_trade_stats(
        db: AsyncSession,
        user_id: int,
        period: str = "today"
    ) -> dict:
        """Get trade statistics for a period"""
        now = datetime.utcnow()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)
        
        result = await db.execute(
            select(Trade).where(
                and_(
                    Trade.user_id == user_id,
                    Trade.status == "CLOSED",
                    Trade.exit_time >= start_date
                )
            )
        )
        
        if period == "yesterday":
            result = await db.execute(
                select(Trade).where(
                    and_(
                        Trade.user_id == user_id,
                        Trade.status == "CLOSED",
                        Trade.exit_time >= start_date,
                        Trade.exit_time < end_date
                    )
                )
            )
        
        trades = result.scalars().all()
        
        total_trades = len(trades)
        win_count = sum(1 for t in trades if t.pnl and t.pnl > 0)
        loss_count = sum(1 for t in trades if t.pnl and t.pnl <= 0)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        net_pnl = sum(t.pnl for t in trades if t.pnl)
        
        return {
            "total_trades": total_trades,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": round(win_rate, 2),
            "net_pnl": round(net_pnl, 2) if net_pnl else 0
        }
