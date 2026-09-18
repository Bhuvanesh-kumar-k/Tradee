from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TradeResponse(BaseModel):
    id: int
    user_id: int
    coin_pair: str
    direction: str
    entry_price: float
    leverage: int
    margin_used: float
    take_profit: float
    stop_loss: float
    liquidation_price: float
    expected_net_roi: float
    timeframe: str
    status: str
    exit_price: Optional[float]
    exit_reason: Optional[str]
    pnl: Optional[float]
    pnl_percentage: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    signal_source: Optional[str]
    ai_verdict: Optional[str]
    is_high_risk: bool
    
    class Config:
        from_attributes = True


class ManualCloseRequest(BaseModel):
    trade_id: int


class TradeStats(BaseModel):
    total_trades: int
    win_count: int
    loss_count: int
    win_rate: float
    net_pnl: float
