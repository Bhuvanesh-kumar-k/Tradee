from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScannerLogResponse(BaseModel):
    id: int
    user_id: int
    coin_pair: str
    timeframe: str
    trend_status: Optional[str]
    signal_detected: Optional[str]
    checklist_passed: Optional[dict]
    ema20: Optional[float]
    ema50: Optional[float]
    ema200: Optional[float]
    rsi: Optional[float]
    macd_hist: Optional[float]
    adx: Optional[float]
    atr: Optional[float]
    scan_time: datetime
    cycle_number: Optional[int]
    
    class Config:
        from_attributes = True


class SingleCoinCheckRequest(BaseModel):
    coin_pair: str


class CoinAnalysisResult(BaseModel):
    coin_pair: str
    timeframes: List[dict]
    overall_signal: Optional[str]
    best_timeframe: Optional[str]
    entry_price: Optional[float]
    take_profit: Optional[float]
    stop_loss: Optional[float]
    leverage: Optional[int]
    expected_roi: Optional[float]
