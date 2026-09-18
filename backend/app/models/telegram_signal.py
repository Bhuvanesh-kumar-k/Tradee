from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func
from app.core.database import Base


class TelegramSignal(Base):
    __tablename__ = "telegram_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Parsed Signal Data
    coin_pair = Column(String, nullable=True)
    direction = Column(String, nullable=True)  # LONG, SHORT
    leverage = Column(String, nullable=True)
    entry_zone = Column(String, nullable=True)
    take_profit_targets = Column(JSON, nullable=True)  # List of TP levels
    stop_loss = Column(String, nullable=True)
    
    # Raw Message
    channel_name = Column(String, nullable=True)
    channel_id = Column(String, nullable=True)
    message_id = Column(Integer, nullable=True)
    raw_message = Column(Text, nullable=True)
    
    # AI Analysis
    ai_verdict = Column(String, nullable=True)  # APPROVED, REJECTED, NEUTRAL
    ai_reasoning = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    # Market Context at Signal Time
    market_trend = Column(String, nullable=True)
    indicator_confluence = Column(JSON, nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False)
    is_executed = Column(Boolean, default=False)
    trade_id = Column(Integer, nullable=True)
    
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
