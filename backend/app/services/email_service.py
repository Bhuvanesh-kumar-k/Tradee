import random
import aiosmtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings


def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return str(random.randint(100000, 999999))


async def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP email via SMTP"""
    try:
        message = EmailMessage()
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email
        message["Subject"] = "Your Crypto Trading Platform Verification Code"
        
        body = f"""
        <html>
        <body>
            <h2>Crypto Trading Platform - Email Verification</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from Crypto Trading Platform. 
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """
        message.set_content(body, subtype="html")
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
            timeout=10
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False


def get_otp_expiry() -> datetime:
    """Get OTP expiry time (10 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=10)
