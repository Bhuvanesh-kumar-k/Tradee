from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import OTPRequest, OTPVerify, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import create_otp, verify_otp_and_register, login_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(
    request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for email verification"""
    success = await create_otp(db, request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerify,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP and register new user"""
    user = await verify_otp_and_register(
        db,
        request.email,
        request.otp_code,
        request.password,
        request.name,
        request.experience_level
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP, or user already exists"
        )
    
    from app.core.security import create_access_token
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    result = await login_user(db, request.email, request.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        user=UserResponse.model_validate(result["user"])
    )
