from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)  # Beginner, Intermediate, Pro
    
    # Margin Settings
    custom_margin_allocation = Column(Float, nullable=True)  # If None, use 20-25% of balance
    scan_interval_minutes = Column(Integer, default=5)  # 3, 5, 7, 10, 15, 30
    
    # AI Settings (provider preference only, keys stored client-side)
    ai_provider = Column(String, default="None")  # None, Gemini, Copilot, OpenAI
    ai_enabled = Column(Boolean, default=False)
    
    # Telegram Settings (channels only, credentials stored client-side)
    telegram_channels = Column(JSON, nullable=True)  # List of channel IDs/usernames
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Legal Terms
    terms_accepted = Column(Boolean, default=False, nullable=False)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Trading Settings
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    preferred_currency = Column(String, default="INR", nullable=False)  # "INR" or "USDT"
    trading_timeframes = Column(JSON, default=list, nullable=False)  # List of allowed execution timeframes (e.g., ["1h", "2h", "4h", "8h", "1d"])
