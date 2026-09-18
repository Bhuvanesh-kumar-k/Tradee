import os

# ==============================================================================
# COINDCX API CREDENTIALS
# ==============================================================================
API_KEY = os.getenv("COINDCX_API_KEY", "cde56a7cd9e156b376d3fe8338ce2af962342dbedd50bb36")
API_SECRET = os.getenv("COINDCX_API_SECRET", "d69c40dceb3db723de2e6a2672da4ee61319552f3cf10d92492ecdc0909304be")

# ==============================================================================
# API ENDPOINTS & HEADERS
# ==============================================================================
BASE_URL = "https://api.coindcx.com"
PUBLIC_URL = "https://public.coindcx.com/market_data/candles"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
}

# ==============================================================================
# MARKET UNIVERSE
# ==============================================================================
# Benchmark pair for the macro regime filter
BTC_PAIR = "B-BTC_USDT"

# High-liquidity futures pairs to analyze
COINS = [
    "B-BTC_USDT",
    "B-ETH_USDT",
    "B-SOL_USDT",
    "B-DOGE_USDT",
    "B-BNB_USDT",
    "B-XRP_USDT",
    "B-ADA_USDT"
]

# High-impact swing timeframes
TIMEFRAMES = ["4h", "8h", "1d"]

# ==============================================================================
# RISK, POSITION & EXECUTION MANAGEMENT
# ==============================================================================
# Wallet risk allocation (25% per trade margin | 75% retained safely in wallet)
RISK_PER_TRADE = 0.25

# Minimum required Net ROI threshold after round-trip taker fees
MIN_PROFIT_ROI = 0.20

# Minimum position notional size (Margin * Leverage) to satisfy exchange order minimums
MIN_ORDER_NOTIONAL = 15.0

# CoinDCX Futures Standard Fee (~0.05% taker fee each side; 0.1% round-trip)
COINDCX_TAKER_FEE = 0.0005

# Polling Interval (in seconds) for continuous monitoring (5 minutes = 300s)
LOOP_INTERVAL_SECONDS = 300
