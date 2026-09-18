import pandas as pd
import numpy as np
# Preserving existing indicator logic from Traders/indicators.py


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI) using Wilder's smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculates MACD Line, Signal Line, and MACD Histogram."""
    exp1 = calculate_ema(series, fast)
    exp2 = calculate_ema(series, slow)
    macd_line = exp1 - exp2
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift()).abs()
    tr3 = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()


def calculate_volume_sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Calculates Simple Moving Average of Volume for breakout confirmation."""
    return series.rolling(window=period, min_periods=period).mean()


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average Directional Index (ADX) to filter out choppy/sideways markets.
    ADX >= 20 confirms an active trend; ADX < 20 indicates sideways consolidation.
    """
    df = df.copy()
    high_diff = df["high"].diff()
    low_diff = -df["low"].diff()

    # Directional Movement (+DM and -DM)
    pos_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
    neg_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)

    # True Range
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift()).abs()
    tr3 = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's Smoothing
    atr_smooth = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    pos_dm_smooth = pd.Series(pos_dm, index=df.index).ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    neg_dm_smooth = pd.Series(neg_dm, index=df.index).ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    # Directional Indicators (+DI and -DI)
    pos_di = 100 * (pos_dm_smooth / (atr_smooth + 1e-9))
    neg_di = 100 * (neg_dm_smooth / (atr_smooth + 1e-9))

    # Directional Movement Index (DX) and ADX
    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di + 1e-9)
    adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return adx


def get_dynamic_swing_levels(df: pd.DataFrame, live_price: float, atr: float):
    """
    Scans across 5, 10, and 15 closed candles to pick the most balanced structural level.
    Ensures the stop is at least 0.8x ATR away (noise protection) but caps it at 3.0x ATR.
    """
    windows = [5, 10, 15]
    best_swing_low = None
    best_swing_high = None

    # Evaluate Long Stop Loss candidate (Swing Low)
    for w in windows:
        if len(df) < w + 2:
            continue
        recent_closed = df.iloc[-(w + 1):-1]
        candidate_low = float(recent_closed["low"].min())
        distance = live_price - candidate_low
        
        # Accept if distance is at least 0.8 * ATR from entry
        if distance >= (0.8 * atr) and distance <= (3.0 * atr):
            best_swing_low = candidate_low
            break

    # Evaluation fallback if all windows were too close or too far
    if best_swing_low is None:
        recent_5 = df.iloc[-6:-1]
        best_swing_low = float(recent_5["low"].min())

    # Evaluate Short Stop Loss candidate (Swing High)
    for w in windows:
        if len(df) < w + 2:
            continue
        recent_closed = df.iloc[-(w + 1):-1]
        candidate_high = float(recent_closed["high"].max())
        distance = candidate_high - live_price
        
        if distance >= (0.8 * atr) and distance <= (3.0 * atr):
            best_swing_high = candidate_high
            break

    if best_swing_high is None:
        recent_5 = df.iloc[-6:-1]
        best_swing_high = float(recent_5["high"].max())

    return best_swing_low, best_swing_high


def calculate_liquidation_price(entry_price: float, leverage: int, direction: str, mm_rate: float = 0.005) -> float:
    """
    Computes theoretical liquidation price under isolated margin.
    mm_rate: Standard maintenance margin rate (~0.5% for major pairs).
    """
    if direction == "LONG":
        # Liq Price = Entry * (1 - (1 / Leverage) + mm_rate)
        liq_price = entry_price * (1.0 - (1.0 / leverage) + mm_rate)
        return max(0.0, liq_price)
    else:
        # Liq Price = Entry * (1 + (1 / Leverage) - mm_rate)
        liq_price = entry_price * (1.0 + (1.0 / leverage) - mm_rate)
        return liq_price


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Master indicator processor for candle DataFrames."""
    df = df.copy()

    # 1. Trend Indicators (EMA 20, 50, 200)
    df["ema20"] = calculate_ema(df["close"], 20)
    df["ema50"] = calculate_ema(df["close"], 50)
    df["ema200"] = calculate_ema(df["close"], 200)

    # 2. Momentum Indicators
    df["rsi"] = calculate_rsi(df["close"], 14)
    macd, signal, hist = calculate_macd(df["close"], 12, 26, 9)
    df["macd"] = macd
    df["macdsignal"] = signal
    df["macdhist"] = hist

    # 3. Volatility, Volume, and Trend Strength
    df["atr"] = calculate_atr(df, 14)
    df["vol_sma20"] = calculate_volume_sma(df["volume"], 20)
    df["adx"] = calculate_adx(df, 14)

    return df
