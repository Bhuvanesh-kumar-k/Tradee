from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import httpx
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import AcceptTermsRequest

router = APIRouter(prefix="/system", tags=["System & Legal"])

@router.get("/terms")
async def get_legal_terms():
    """Returns statutory disclaimers under Indian Law for Virtual Digital Assets (VDAs)"""
    return {
        "title": "Mandatory Risk Disclosure, Disclaimer & Terms of Use",
        "jurisdiction": "India (Virtual Digital Assets / VDA Framework)",
        "effective_date": "2026-09-01",
        "warning_banner": "⚠️ HIGH-RISK WARNING: Cryptos and Virtual Digital Assets (VDAs) are highly volatile, unregulated in India, and carry significant capital loss risks.",
        "terms": [
            {
                "section": "1. Nature of the Software",
                "content": "This application is strictly a self-hosted, technical algorithmic tool and computational utility. It provides automated execution based solely on user-provided parameters, exchange API keys, and pre-set technical indicator logic. It is NOT an asset management platform, mutual fund, collective investment scheme, or bank."
            },
            {
                "section": "2. No Financial Advice & Non-SEBI Registered Entity",
                "content": "Neither the developer, publisher, nor platform operators are registered Investment Advisers (IA) or Research Analysts (RA) under the Securities and Exchange Board of India (SEBI) Act, 1992, or licensed financial entities under the Reserve Bank of India (RBI). No content, automated signal, or AI analysis constitutes investment, trading, or financial advice."
            },
            {
                "section": "3. Absolute Absence of Profit Guarantee",
                "content": "Algorithmic execution carries substantial risk. The user acknowledges that cryptocurrency futures involve high leverage where entire capital balances can be liquidated within seconds due to slippage, spread widening, or exchange API downtime. There is NO GUARANTEE of capital preservation, return on investment (ROI), or win rate."
            },
            {
                "section": "4. Sole User Liability & Assumption of Risk",
                "content": "All trades executed via your linked CoinDCX API keys are initiated under your sole discretion and custody. You retain full responsibility for all profits, losses, margin calls, liquidations, and applicable Indian tax obligations (including Section 115BBH 30% tax on VDA profits and Section 194S 1% TDS)."
            },
            {
                "section": "5. Mandatory Exit Condition",
                "content": "If you do not agree to these terms, acknowledge the risks, and accept sole responsibility for your capital, you must immediately decline and terminate use of this application. Acceptance is an absolute prerequisite to unlocking trading functionality."
            }
        ]
    }

@router.post("/accept-terms")
async def accept_terms(
    request: AcceptTermsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Records the user's explicit consent to the legal terms and risk disclaimers"""
    if not request.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms must be accepted to use this application."
        )
    current_user.terms_accepted = True
    current_user.terms_accepted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    return {"status": "success", "terms_accepted": True, "accepted_at": current_user.terms_accepted_at}

@router.get("/about")
async def get_about_platform():
    """Provides technical documentation of what the engine does, monitors, and analyzes"""
    return {
        "app_name": "Autonomous Crypto Quantitative Trading Agent",
        "engine_architecture": "Deterministic Multi-Timeframe Algorithmic Rules + Optional AI Signal Reasoning",
        "description": "An institutional-grade trading system designed to automate futures market analysis on CoinDCX and filter high-probability setups while enforcing strict risk boundaries.",
        "core_capabilities": [
            "Autonomous 24/7 background scanning of high-liquidity crypto futures markets.",
            "Automated order bracket management (Margin, Leverage, TP, SL, Liquidation Buffers).",
            "Multi-tenant Telethon MTProto listener for Telegram trading signals.",
            "AI-powered signal reasoning (Gemini / GPT-4o-mini) to cross-reference calls against live indicator data.",
            "Macro news volatility circuit breaker pausing scans around high-impact US economic releases (CPI, FOMC, NFP)."
        ],
        "analytical_checks": {
            "macro_regime": "Evaluates Bitcoin (BTC_USDT) on 1-Day chart against EMA 50 & EMA 200. Blocks Altcoin Longs if macro trend is bearish.",
            "timeframe_confluence": "Requires simultaneous alignment across 1-Day, 1-Hour, 4-Hour, and 8-Hour candles before triggering entries.",
            "trend_momentum": "EMA 20/50/200 trend alignment and MACD Histogram momentum positivity checks on confirmed candle closes.",
            "choppiness_filter": "ADX(14) >= 20 threshold to eliminate sideways whipsaw markets.",
            "volume_support": "Requires candle volume to exceed at least 80% of the 20-period Volume SMA.",
            "risk_containment": "Enforces dynamic swing-level stop losses (0.8x to 3.0x ATR) maintaining a mandatory >=40% buffer above/below the liquidation price, targeting >=20% Net ROI after fees."
        }
    }


@router.get("/key-guides")
async def get_key_guides():
    """Step-by-step setup guides for external credentials and API keys"""
    return {
        "coindcx": {
            "title": "CoinDCX Futures API Credentials",
            "steps": [
                "1. Log in to CoinDCX ([https://coindcx.com](https://coindcx.com)) in your browser.",
                "2. Click your Profile icon (top-right) -> select 'Profile'.",
                "3. In the left menu, select 'API Dashboard'.",
                "4. Click 'Create A New One' / 'Create API Key'.",
                "5. Enter a label (e.g. 'TradeBot') and complete OTP verification.",
                "6. Grant 'Futures Trading' permissions (leave 'Withdrawal' UNCHECKED for safety).",
                "7. Copy both the API Key and Secret Key immediately and paste them into your profile."
            ]
        },
        "gemini": {
            "title": "Google Gemini API Key (Recommended & Free)",
            "steps": [
                "1. Open Google AI Studio ([https://aistudio.google.com](https://aistudio.google.com)).",
                "2. Sign in with any standard Google account.",
                "3. Click 'Get API key' from the left sidebar.",
                "4. Click 'Create API key' and select your default project.",
                "5. Copy the generated API key and paste it here. No credit card is required."
            ]
        },
        "openai": {
            "title": "OpenAI API Key (Optional)",
            "steps": [
                "1. Go to OpenAI Platform ([https://platform.openai.com](https://platform.openai.com)).",
                "2. Sign in and navigate to Settings -> 'API Keys'.",
                "3. Click 'Create new secret key', enter a name, and copy the key.",
                "4. Paste the key here. Note: Requires a paid OpenAI developer balance ($5 minimum)."
            ]
        },
        "telegram": {
            "title": "Telegram MTProto API ID & Hash",
            "steps": [
                "1. Visit [https://my.telegram.org](https://my.telegram.org) in your web browser.",
                "2. Log in with your personal phone number (including country code) and enter the code sent to your Telegram app.",
                "3. Select 'API development tools'.",
                "4. Enter an App title and Short name (e.g., 'SignalScanner').",
                "5. Submit the form to generate your numeric 'api_id' and alphanumeric 'api_hash'.",
                "6. Copy and paste both values into their respective fields."
            ]
        }
    }


@router.get("/conversion-rate")
async def get_conversion_rate():
    """Returns current INR to USDT conversion rate from CoinDCX"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.coindcx.com/exchange/ticker")
            if response.status_code == 200:
                data = response.json()
                # Find INR/USDT pair
                for ticker in data:
                    if ticker.get("market") == "INRUSDT":
                        return {
                            "currency_pair": "INR/USDT",
                            "rate": ticker.get("last_price"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                # Fallback to hardcoded rate if API fails
                return {
                    "currency_pair": "INR/USDT",
                    "rate": 0.012,  # Approximate fallback rate
                    "timestamp": datetime.utcnow().isoformat(),
                    "note": "Fallback rate used - API did not return INR/USDT pair"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to fetch conversion rate from CoinDCX"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error fetching conversion rate: {str(e)}"
        )