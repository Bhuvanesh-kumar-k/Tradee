from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Email Delivery Configuration
    RESEND_API_KEY: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_EMAIL: str = "bhuvaneshkumark.kec@gmail.com"
    SMTP_PASSWORD: str = ""
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./crypto_trading.db"
    
    # CoinDCX API Configuration (defaults)
    COINDCX_API_KEY: Optional[str] = None
    COINDCX_API_SECRET: Optional[str] = None
    
    # AI API Configuration
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    COPILOT_API_KEY: Optional[str] = None
    
    # Telegram Configuration
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    
    # CoinDCX API Endpoints
    COINDCX_BASE_URL: str = "https://api.coindcx.com"
    COINDCX_PUBLIC_URL: str = "https://public.coindcx.com/market_data/candles"
    
    # Trading Configuration
    DEFAULT_RISK_PER_TRADE: float = 0.25
    MIN_PROFIT_ROI: float = 0.20
    COINDCX_TAKER_FEE: float = 0.0005
    MIN_ORDER_NOTIONAL: float = 15.0
    
    # Default Coin Universe
    BTC_PAIR: str = "B-BTC_USDT"
    DEFAULT_COINS: list = [
        "B-BTC_USDT",
        "B-ETH_USDT",
        "B-SOL_USDT",
        "B-DOGE_USDT",
        "B-BNB_USDT",
        "B-XRP_USDT",
        "B-ADA_USDT"
    ]
    DEFAULT_TIMEFRAMES: list = ["4h", "8h", "1d"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
