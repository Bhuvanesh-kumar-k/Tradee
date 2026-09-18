# Crypto Trading Platform - Backend

Production-grade multi-user cryptocurrency futures trading platform backend.

## Features

- **Multi-User Authentication**: Email OTP registration/login with JWT tokens
- **Encrypted Credentials**: AES-256 encryption for API keys and secrets
- **Technical Analysis Engine**: EMA, RSI, MACD, ATR, ADX indicators
- **Multi-Timeframe Strategy**: 1h, 4h, 8h, 1d confluence analysis
- **Macro News Circuit Breaker**: Automatic trading pause during high-impact events
- **Telegram Signal Listener**: MTProto client for channel signal parsing
- **AI Integration**: Gemini, OpenAI, Copilot support for signal validation
- **CoinDCX Execution**: Automated futures order management
- **Position Tracking**: Real-time PnL monitoring and early exit alerts
- **WebSocket Streams**: Live trading updates and scanner logs

## Installation

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Required environment variables in `.env`:

- `SMTP_EMAIL`: Your Gmail address for OTP emails
- `SMTP_PASSWORD`: Gmail App Password (generate from Google Account settings)
- `SECRET_KEY`: Random secret key for JWT signing
- `DATABASE_URL`: SQLite or PostgreSQL connection string

## Running the Server

```bash
python main.py
```

Server will start on `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /api/v1/auth/request-otp` - Request OTP for email verification
- `POST /api/v1/auth/verify-otp` - Verify OTP and register user
- `POST /api/v1/auth/login` - Login with email and password

### Settings
- `GET /api/v1/settings/me` - Get user settings
- `PUT /api/v1/settings/me` - Update user settings
- `POST /api/v1/settings/verify-ai-key` - Verify AI API key

### Scanner
- `GET /api/v1/scanner/status` - Get scanner status and news events
- `POST /api/v1/scanner/check-coin` - Analyze a single coin
- `GET /api/v1/scanner/logs` - Get scanner logs

### Trades
- `GET /api/v1/trades/active` - Get active positions
- `GET /api/v1/trades/history` - Get trade history
- `GET /api/v1/trades/stats` - Get trade statistics
- `POST /api/v1/trades/close` - Manually close position

### Telegram
- `POST /api/v1/telegram/start` - Start Telegram listener
- `POST /api/v1/telegram/stop` - Stop Telegram listener
- `GET /api/v1/telegram/signals` - Get received signals
- `GET /api/v1/telegram/status` - Get listener status

### WebSocket
- `WS /api/v1/ws/live-updates?token={token}&user_id={user_id}` - Real-time updates

## Architecture

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core logic (indicators, strategy, market data)
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   └── services/      # Business logic services
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
└── .env.example       # Environment template
```

## Security

- All sensitive API keys encrypted at rest using AES-256
- JWT tokens for authentication
- CORS middleware for cross-origin requests
- Input validation using Pydantic

## License

Proprietary - All rights reserved
