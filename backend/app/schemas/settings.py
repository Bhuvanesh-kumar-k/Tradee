from pydantic import BaseModel, Field
from typing import Optional, List


class CoinDCXSettings(BaseModel):
    api_key: str
    api_secret: str


class MarginSettings(BaseModel):
    custom_margin_allocation: Optional[float] = Field(None, ge=0)
    risk_percentage_per_trade: Optional[float] = Field(0.25, ge=0.03, le=0.50)
    scan_interval_minutes: int = Field(5, ge=3, le=30)


class AISettings(BaseModel):
    provider: str = Field("None", pattern="^(None|Gemini|Copilot|OpenAI)$")
    api_key: Optional[str] = None


class TelegramSettings(BaseModel):
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    channels: Optional[List[str]] = None


class TradingSettings(BaseModel):
    auto_trading_enabled: Optional[bool] = False
    preferred_currency: Optional[str] = Field("INR", pattern="^(INR|USDT)$")
    trading_timeframes: Optional[List[str]] = Field(default_factory=lambda: ["1h", "2h", "4h", "8h", "1d"])


class UserSettingsUpdate(BaseModel):
    coindcx: Optional[CoinDCXSettings] = None
    margin: Optional[MarginSettings] = None
    ai: Optional[AISettings] = None
    telegram: Optional[TelegramSettings] = None
    trading: Optional[TradingSettings] = None


class AIKeyVerify(BaseModel):
    provider: str = Field(..., pattern="^(Gemini|Copilot|OpenAI)$")
    api_key: str
