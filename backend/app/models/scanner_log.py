from sqlalchemy import Column, Integer, String, DateTime, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base


class ScannerLog(Base):
    __tablename__ = "scanner_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    coin_pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    
    # Analysis Results
    trend_status = Column(String, nullable=True)  # BULLISH, BEARISH, NEUTRAL
    signal_detected = Column(String, nullable=True)  # LONG, SHORT, NONE
    checklist_passed = Column(JSON, nullable=True)
    
    # Indicator Values
    ema20 = Column(Float, nullable=True)
    ema50 = Column(Float, nullable=True)
    ema200 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    
    # Metadata
    scan_time = Column(DateTime(timezone=True), server_default=func.now())
    cycle_number = Column(Integer, nullable=True)
