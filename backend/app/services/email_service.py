import random
import traceback
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings


def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return str(random.randint(100000, 999999))


async def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP email using Resend HTTPS API (Cloud-safe) with SMTP fallback"""
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0D1117; color: #E6EDF3; padding: 24px;">
        <div style="max-width: 480px; margin: 0 auto; background-color: #161B22; border-radius: 12px; padding: 32px; border: 1px solid #30363D;">
            <h2 style="color: #00D4AA; margin-top: 0;">Tradee Verification Code</h2>
            <p style="color: #8B949E; font-size: 14px;">Enter the code below in the Tradee app to complete your registration:</p>
            <div style="background-color: #0D1117; padding: 16px; text-align: center; border-radius: 8px; margin: 24px 0;">
                <span style="color: #00D4AA; font-size: 36px; font-weight: bold; letter-spacing: 8px;">{otp_code}</span>
            </div>
            <p style="color: #8B949E; font-size: 13px;">This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
            <hr style="border: 0; border-top: 1px solid #30363D; margin: 24px 0;">
            <p style="color: #8B949E; font-size: 11px; margin: 0;">Automated message from Tradee Platform. Do not reply.</p>
        </div>
    </body>
    </html>
    """

    # 1. Primary: Use Resend HTTPS API if key is provided (never blocked by Render)
    if settings.RESEND_API_KEY:
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY.strip()
            params = {
                "from": "Tradee <onboarding@resend.dev>",
                "to": [email],
                "subject": f"{otp_code} is your Tradee verification code",
                "html": html_content,
            }
            resend.Emails.send(params)
            print(f"✅ OTP email sent successfully to {email} via Resend HTTPS API")
            return True
        except Exception as e:
            print(f"❌ Resend API failed: {e}")
            traceback.print_exc()

    # 2. Secondary Fallback: SMTP socket
    try:
        import aiosmtplib
        from email.message import EmailMessage

        clean_password = settings.SMTP_PASSWORD.replace(" ", "").strip()
        message = EmailMessage()
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email
        message["Subject"] = f"{otp_code} is your Tradee verification code"
        message.set_content(html_content, subtype="html")

        is_ssl = int(settings.SMTP_PORT) == 465
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=int(settings.SMTP_PORT),
            username=settings.SMTP_EMAIL.strip(),
            password=clean_password,
            use_tls=is_ssl,
            start_tls=not is_ssl,
            timeout=10
        )
        print(f"✅ OTP email sent successfully to {email} via SMTP")
        return True
    except Exception as e:
        print(f"❌ SMTP failed to send OTP to {email}: {e}")
        traceback.print_exc()
        return False


def get_otp_expiry() -> datetime:
    """Get OTP expiry time (10 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=10)
