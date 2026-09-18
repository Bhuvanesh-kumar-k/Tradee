from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from app.models.user import User
from app.models.otp import OTP
from app.core.security import verify_password, get_password_hash, create_access_token
from app.services.email_service import generate_otp, send_otp_email, get_otp_expiry


async def create_otp(db: AsyncSession, email: str) -> bool:
    """Create and send OTP for email verification"""
    # Delete any existing unused OTPs for this email
    await db.execute(
        select(OTP).where(OTP.email == email, OTP.is_used == False)
    )
    result = await db.execute(
        select(OTP).where(OTP.email == email, OTP.is_used == False)
    )
    existing_otps = result.scalars().all()
    for otp in existing_otps:
        otp.is_used = True
    
    # Generate new OTP
    otp_code = generate_otp()
    new_otp = OTP(
        email=email,
        otp_code=otp_code,
        expires_at=get_otp_expiry()
    )
    db.add(new_otp)
    await db.commit()
    
    # Send email
    return await send_otp_email(email, otp_code)


async def verify_otp_and_register(
    db: AsyncSession,
    email: str,
    otp_code: str,
    password: str,
    name: Optional[str] = None,
    experience_level: Optional[str] = None
) -> Optional[User]:
    """Verify OTP and register new user"""
    # Find valid OTP
    result = await db.execute(
        select(OTP).where(
            OTP.email == email,
            OTP.otp_code == otp_code,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        )
    )
    otp = result.scalar_one_or_none()
    
    if not otp:
        return None
    
    # Mark OTP as used
    otp.is_used = True
    
    # Check if user already exists
    existing_user = await db.execute(
        select(User).where(User.email == email)
    )
    if existing_user.scalar_one_or_none():
        await db.commit()
        return None
    
    # Create new user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        name=name,
        experience_level=experience_level,
        is_verified=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return user


async def login_user(db: AsyncSession, email: str, password: str) -> Optional[dict]:
    """Login user and return access token"""
    user = await authenticate_user(db, email, password)
    if not user:
        return None
    
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "user": user
    }
