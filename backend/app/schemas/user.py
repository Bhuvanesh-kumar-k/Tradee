from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class AcceptTermsRequest(BaseModel):
    accepted: bool


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    experience_level: Optional[str] = Field(None, pattern="^(Beginner|Intermediate|Pro)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    experience_level: Optional[str] = Field(None, pattern="^(Beginner|Intermediate|Pro)$")
    auto_trading_enabled: Optional[bool] = None
    preferred_currency: Optional[str] = Field(None, pattern="^(INR|USDT)$")
    trading_timeframes: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    experience_level: Optional[str]
    created_at: datetime
    is_active: bool
    is_verified: bool
    terms_accepted: bool = False
    terms_accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    experience_level: Optional[str] = Field(None, pattern="^(Beginner|Intermediate|Pro)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
