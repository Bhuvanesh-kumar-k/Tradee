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
    """Periodic market scanning task for all users"""
    try:
        async with AsyncSessionLocal() as db:
            # Get all active users
            result = await db.execute(
                select(User).where(
                    User.is_active == True
                )
            )
            users = result.scalars().all()
            
            for user in users:
                try:
                    # Check if trading is frozen due to news
                    frozen_status = circuit_breaker.get_frozen_status_message()
                    if frozen_status:
                        await send_system_status(
                            user.id,
                            "frozen",
                            frozen_status
                        )
                        continue
                    
                    # Get user's capital allocation
                    capital = user.custom_margin_allocation
                    if capital is None:
                        executor = await get_user_executor(user)
                        if executor:
                            balance_data = await executor.get_futures_balance()
                            if balance_data:
                                total_balance = balance_data.get("balance", 0) or balance_data.get("total_balance", 0)
                                if total_balance > 0:
                                    risk_pct = getattr(user, "risk_percentage_per_trade", 0.25)
                                    capital = total_balance * risk_pct
                    
                    if capital is None or capital < 20:
                        capital = 20.0
                    
                    # Run market scan with 1-hour timeframe enabled
                    candidates = await evaluate_all_markets(
                        capital=capital,
                        coins=settings.DEFAULT_COINS,
                        user_timeframes=["1h", "4h", "8h", "1d"]
                    )
                    
                    # Log candidates (in production, would save to database and notify user)
                    if candidates:
                        print(f"Found {len(candidates)} trade candidates for user {user.id}")
                    
                except Exception as e:
                    print(f"Market scan failed for user {user.id}: {e}")
            
    except Exception as e:
        print(f"Market scan task error: {e}")


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
    """User-specific market scan task"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return
            
            # Check scan interval
            interval_minutes = user.scan_interval_minutes or 5
            
            # Get capital
            capital = user.custom_margin_allocation
            if capital is None:
                executor = await get_user_executor(user)
                if executor:
                    balance_data = await executor.get_futures_balance()
                    if balance_data:
                        total_balance = balance_data.get("balance", 0) or balance_data.get("total_balance", 0)
                        if total_balance > 0:
                            risk_pct = getattr(user, "risk_percentage_per_trade", 0.25)
                            capital = total_balance * risk_pct
            
            if capital is None or capital < 20:
                capital = 20.0
            
            # Run scan with 1-hour timeframe
            candidates = await evaluate_all_markets(
                capital=capital,
                coins=settings.DEFAULT_COINS,
                user_timeframes=["1h", "4h", "8h", "1d"]
            )
            
    except Exception as e:
        print(f"User-specific scan failed for user {user_id}: {e}")


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
