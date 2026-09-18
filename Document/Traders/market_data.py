import time
import requests
import pandas as pd
from config import PUBLIC_URL, HEADERS

def fetch_raw_candles(pair: str, interval: str = "1h", limit: int = 1000, start_time: int = None) -> pd.DataFrame | None:
    url = f"{PUBLIC_URL}?pair={pair}&interval={interval}&limit={limit}"
    if start_time:
        url += f"&startTime={start_time}"
        
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return None
            
        data = res.json()
        if not isinstance(data, list) or len(data) < 1:
            return None

        parsed = []
        for c in reversed(data):
            if isinstance(c, dict) and "close" in c:
                parsed.append([
                    int(c.get("time", 0)),
                    float(c["open"]),
                    float(c["high"]),
                    float(c["low"]),
                    float(c["close"]),
                    float(c.get("volume", 0.0))
                ])
                
        df = pd.DataFrame(parsed, columns=["time", "open", "high", "low", "close", "volume"])
        return df

    except Exception as e:
        print(f"  ❌ [{pair} | {interval}] Connection error: {e}")
        return None

def fetch_current_price(pair: str) -> float | None:
    df = fetch_raw_candles(pair, interval="1m", limit=1)
    if df is not None and not df.empty:
        return float(df.iloc[-1]["close"])
    df = fetch_raw_candles(pair, interval="1h", limit=1)
    if df is not None and not df.empty:
        return float(df.iloc[-1]["close"])
    return None

def fetch_deep_1h_candles(pair: str) -> pd.DataFrame | None:
    df_recent = fetch_raw_candles(pair, interval="1h", limit=1000)
    if df_recent is None or len(df_recent) < 50:
        return None

    oldest_time = int(df_recent.iloc[0]["time"])
    prior_start_time = oldest_time - (1000 * 60 * 60 * 1000)

    df_prior = fetch_raw_candles(pair, interval="1h", limit=1000, start_time=prior_start_time)
    
    if df_prior is not None and len(df_prior) > 0:
        combined = pd.concat([df_prior, df_recent], ignore_index=True)
        combined = combined.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        return combined

    return df_recent

def fetch_candles(pair: str, interval: str) -> pd.DataFrame | None:
    if interval in ["4h", "8h"]:
        df_1h = fetch_deep_1h_candles(pair)
        if df_1h is None or len(df_1h) < 120:
            return None
            
        df_1h["datetime"] = pd.to_datetime(df_1h["time"], unit="ms")
        df_1h.set_index("datetime", inplace=True)
        
        rule = "4h" if interval == "4h" else "8h"
        resampled = df_1h.resample(rule).agg({
            "time": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna().reset_index(drop=True)
        
        return resampled

    if interval == "1d":
        df_daily = fetch_raw_candles(pair, interval="1d", limit=250)
        if df_daily is None or len(df_daily) < 50:
            return None
            
        df_daily = df_daily.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        df_daily["datetime"] = pd.to_datetime(df_daily["time"], unit="ms")
        df_daily.set_index("datetime", inplace=True)
        
        resampled_1d = df_daily.resample("1D").agg({
            "time": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna().reset_index(drop=True)
        
        return resampled_1d

    return fetch_raw_candles(pair, interval=interval, limit=250)
