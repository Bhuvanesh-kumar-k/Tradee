from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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


class TimeframeCheckDetail(BaseModel):
    timeframe: str
    direction: Optional[str] = "NEUTRAL"
    is_setup_valid: bool = False
    passed_checks: List[str] = []
    failed_checks: List[str] = []
    checklist: Dict[str, bool] = {}
    roi: Optional[float] = None
    entry: Optional[float] = None
    tp: Optional[float] = None
    sl: Optional[float] = None
    leverage: Optional[int] = None


class CoinAnalysisResult(BaseModel):
    coin_pair: str
    macro_1d_trend: str
    ltf_1h_trend: str
    btc_macro_trend: str
    timeframes: List[TimeframeCheckDetail]
    overall_signal: str
    best_timeframe: Optional[str] = None
    entry_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    leverage: Optional[int] = None
    expected_roi: Optional[float] = None
    summary_reason: str
