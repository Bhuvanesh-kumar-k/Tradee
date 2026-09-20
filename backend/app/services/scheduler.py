from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
from typing import Dict, Optional
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings
from app.core.strategy import evaluate_all_markets
from app.core.news_calendar import circuit_breaker
from app.services.position_tracker import PositionTracker
from app.services.coindcx_executor import get_user_executor
from app.models.trade import Trade
from app.api.v1.websocket import send_system_status, send_trade_update


class BackgroundScheduler:
    """Autonomous background scheduler for periodic tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the background scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            print("Background scheduler started")
    
    def shutdown(self):
        """Shutdown the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Background scheduler stopped")
    
    def add_job(self, func, trigger, **kwargs):
        """Add a job to the scheduler"""
        self.scheduler.add_job(func, trigger, **kwargs)
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        self.scheduler.remove_job(job_id)


# Global scheduler instance
background_scheduler = BackgroundScheduler()


async def market_scan_task():
    """Market scanning task - skipped if server does not manage API keys"""
    return


async def position_monitor_task():
    """Periodic position monitoring and PnL updates"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Trade).where(Trade.status == "OPEN")
            )
            active_trades = result.scalars().all()
            
            for trade in active_trades:
                try:
                    # Update PnL
                    await PositionTracker.update_position_pnl(db, trade)
                    
                    # Check exit conditions
                    exit_reason = await PositionTracker.check_exit_conditions(db, trade)
                    if exit_reason:
                        # Close position
                        user_result = await db.execute(select(User).where(User.id == trade.user_id))
                        user = user_result.scalar_one_or_none()
                        if user:
                            executor = await get_user_executor(user)
                            if executor:
                                quantity = (trade.margin_used * trade.leverage) / trade.entry_price
                                await executor.close_position(trade.coin_pair, quantity)
                        
                        await PositionTracker.close_position(db, trade, None, exit_reason)
                        
                        # Notify user via WebSocket
                        await send_trade_update(trade.user_id, {
                            "trade_id": trade.id,
                            "status": "CLOSED",
                            "exit_reason": exit_reason,
                            "pnl": trade.pnl,
                            "pnl_percentage": trade.pnl_percentage
                        })
                
                except Exception as e:
                    print(f"Position monitor failed for trade {trade.id}: {e}")
            
    except Exception as e:
        print(f"Position monitor task error: {e}")


async def news_calendar_update_task():
    """Periodic news calendar update"""
    try:
        # Fetch upcoming economic events
        await circuit_breaker.fetch_economic_calendar(days_ahead=7)
        print("News calendar updated")
        
    except Exception as e:
        print(f"News calendar update error: {e}")


async def user_specific_scan_task(user_id: int):
    """User-specific market scan task - skipped if server does not manage API keys"""
    return


def initialize_scheduler():
    """Initialize all scheduled tasks"""
    # Market scan every 5 minutes
    background_scheduler.add_job(
        market_scan_task,
        IntervalTrigger(minutes=5),
        id='market_scan',
        name='Market Scan',
        replace_existing=True
    )
    
    # Position monitor every 1 minute
    background_scheduler.add_job(
        position_monitor_task,
        IntervalTrigger(minutes=1),
        id='position_monitor',
        name='Position Monitor',
        replace_existing=True
    )
    
    # News calendar update every 6 hours
    background_scheduler.add_job(
        news_calendar_update_task,
        IntervalTrigger(hours=6),
        id='news_calendar',
        name='News Calendar Update',
        replace_existing=True
    )
    
    print("Scheduler initialized with default jobs")
