from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Trade Details
    coin_pair = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # LONG or SHORT
    entry_price = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    margin_used = Column(Float, nullable=False)
    
    # Targets
    take_profit = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    liquidation_price = Column(Float, nullable=False)
    
    # Execution
    expected_net_roi = Column(Float, nullable=False)
    timeframe = Column(String, nullable=False)
    
    # Status
    status = Column(String, default="OPEN")  # OPEN, CLOSED, CANCELLED
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)  # TP, SL, MANUAL, EARLY_EXIT
    pnl = Column(Float, nullable=True)
    pnl_percentage = Column(Float, nullable=True)
    
    # Metadata
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    signal_source = Column(String, nullable=True)  # SCANNER, TELEGRAM, MANUAL
    ai_verdict = Column(Text, nullable=True)
    is_high_risk = Column(Boolean, default=False)
    
    # CoinDCX Order IDs
    coindcx_order_id = Column(String, nullable=True)
    coindcx_position_id = Column(String, nullable=True)


class TradeLog(Base):
    __tablename__ = "trade_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    trade_id = Column(Integer, nullable=True, index=True)
    
    log_type = Column(String, nullable=False)  # SCAN, SIGNAL, ENTRY, EXIT, ALERT
    message = Column(Text, nullable=False)
    trade_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
