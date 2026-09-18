import sys
import pandas as pd
from datetime import datetime

from config import (
    RISK_PER_TRADE,
    MIN_PROFIT_ROI,
    COINDCX_TAKER_FEE,
    BTC_PAIR
)
from market_data import fetch_raw_candles, fetch_candles
from indicators import (
    calculate_all_indicators,
    get_dynamic_swing_levels,
    calculate_liquidation_price
)
from strategy import get_btc_macro_trend

ALL_TIMEFRAMES = ["30m", "1h", "4h", "8h", "1w"]

def fetch_unified_candles(pair: str, interval: str):
    if interval == "30m":
        df_5m = fetch_raw_candles(pair, interval="5m", limit=600)
        if df_5m is not None and len(df_5m) >= 60:
            df_5m["datetime"] = pd.to_datetime(df_5m["time"], unit="ms")
            df_5m.set_index("datetime", inplace=True)
            resampled = df_5m.resample("30min").agg({
                "time": "min",
                "open": lambda x: x.iloc[0] if len(x) > 0 else None,
                "high": "max",
                "low": "min",
                "close": lambda x: x.iloc[-1] if len(x) > 0 else None,
                "volume": "sum"
            }).dropna().reset_index(drop=True)
            return resampled
        return None

    if interval == "1h":
        return fetch_raw_candles(pair, interval="1h", limit=300)

    if interval in ["4h", "8h"]:
        return fetch_candles(pair, interval)

    if interval == "1w":
        df_w = fetch_raw_candles(pair, interval="1w", limit=100)
        if df_w is not None and len(df_w) >= 20:
            return df_w.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        return None

    return None

def get_coin_macro_trend(pair: str) -> str:
    df_1d = fetch_candles(pair, "1d")
    if df_1d is None or len(df_1d) < 100:
        return "NEUTRAL"
    df_1d = calculate_all_indicators(df_1d)
    prev_closed = df_1d.iloc[-2]
    if prev_closed["close"] > prev_closed["ema50"] and prev_closed["close"] > prev_closed["ema200"]:
        return "BULLISH"
    elif prev_closed["close"] < prev_closed["ema50"]:
        return "BEARISH"
    return "NEUTRAL"

def evaluate_complete_pair(pair: str, capital: float, btc_trend: str):
    candidate_trades = []
    allocated_margin = capital * RISK_PER_TRADE

    df_1d = fetch_candles(pair, "1d")
    is_1d_bullish = False
    is_1d_bearish = False
    if df_1d is not None and len(df_1d) >= 100:
        df_1d = calculate_all_indicators(df_1d)
        closed_1d = df_1d.iloc[-2]
        is_1d_bullish = (closed_1d["close"] > closed_1d["ema50"]) and (closed_1d["close"] > closed_1d["ema200"])
        is_1d_bearish = (closed_1d["close"] < closed_1d["ema50"])

    clean_pair = pair.replace("B-", "")

    # Pre-check 1h and 30m trends for execution gate confirmation
    df_1h = fetch_unified_candles(pair, "1h")
    ltf_1h_bullish = False
    ltf_1h_bearish = False
    if df_1h is not None and len(df_1h) >= 50:
        df_1h_ind = calculate_all_indicators(df_1h)
        bar_1h = df_1h_ind.iloc[-2]
        ltf_1h_bullish = bar_1h["close"] > bar_1h["ema50"]
        ltf_1h_bearish = bar_1h["close"] < bar_1h["ema50"]

    for tf in ALL_TIMEFRAMES:
        df = fetch_unified_candles(pair, tf)
        min_required = 20 if tf == "1w" else 50
        if df is None or len(df) < min_required:
            print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> NEUTRAL (Insufficient Candle Data)")
            continue

        df = calculate_all_indicators(df)
        
        closed_bar = df.iloc[-2]
        prior_closed_bar = df.iloc[-3]
        live_entry = float(df.iloc[-1]["close"])
        atr = closed_bar["atr"]

        swing_low, swing_high = get_dynamic_swing_levels(df, live_entry, atr)
        volatility_ratio = atr / live_entry
        leverage = 8 if volatility_ratio < 0.025 else 5

        direction = None
        sl = tp = net_roi = net_profit = commission = liq_price = None
        is_high_risk_macd = False

        long_checklist = {
            "BTC Macro Trend Bullish": (pair == BTC_PAIR or btc_trend == "BULLISH"),
            "1D Trend Confluence (50 & 200 EMA)": is_1d_bullish,
            "Price > EMA50 (Trend Alignment)": closed_bar["close"] > closed_bar["ema50"],
            "ADX >= 20 (Non-Choppy Market)": closed_bar["adx"] >= 20.0,
            "RSI in Pullback Zone (40-60)": (40 <= closed_bar["rsi"] <= 60),
            "MACD Momentum Positive": (closed_bar["macdhist"] > 0 and closed_bar["macdhist"] > prior_closed_bar["macdhist"]),
            "Volume Support (>=80% SMA20)": closed_bar["volume"] >= (closed_bar["vol_sma20"] * 0.80)
        }

        short_checklist = {
            "BTC Macro Trend Bearish": (pair == BTC_PAIR or btc_trend == "BEARISH"),
            "1D Trend Confluence (< 50 EMA)": is_1d_bearish,
            "Price < EMA50 (Trend Alignment)": closed_bar["close"] < closed_bar["ema50"],
            "ADX >= 20 (Non-Choppy Market)": closed_bar["adx"] >= 20.0,
            "RSI in Breakdown Zone (40-62)": (40 <= closed_bar["rsi"] <= 62),
            "MACD Momentum Negative": (closed_bar["macdhist"] < 0 and closed_bar["macdhist"] < prior_closed_bar["macdhist"]),
            "Volume Support (>=80% SMA20)": closed_bar["volume"] >= (closed_bar["vol_sma20"] * 0.80)
        }

        long_non_macd = [v for k, v in long_checklist.items() if "MACD" not in k]
        short_non_macd = [v for k, v in short_checklist.items() if "MACD" not in k]

        if all(long_checklist.values()):
            direction = "LONG"
            is_high_risk_macd = False
            active_checklist = long_checklist.copy()
        elif all(long_non_macd) and not long_checklist["MACD Momentum Positive"]:
            direction = "LONG"
            is_high_risk_macd = True
            active_checklist = long_checklist.copy()
        elif all(short_checklist.values()):
            direction = "SHORT"
            is_high_risk_macd = False
            active_checklist = short_checklist.copy()
        elif all(short_non_macd) and not short_checklist["MACD Momentum Negative"]:
            direction = "SHORT"
            is_high_risk_macd = True
            active_checklist = short_checklist.copy()
        else:
            active_checklist = None

        if direction:
            # Lower-Timeframe (LTF) Gate: Block counter-trend entries on 4h/8h
            ltf_aligned = True
            if tf in ["4h", "8h"]:
                if direction == "LONG" and not ltf_1h_bullish:
                    ltf_aligned = False
                elif direction == "SHORT" and not ltf_1h_bearish:
                    ltf_aligned = False

            if direction == "LONG":
                sl = swing_low - (0.5 * atr)
                risk_distance = live_entry - sl
                tp = live_entry + max(2.5 * risk_distance, 2.5 * atr)
                liq_price = calculate_liquidation_price(live_entry, leverage, "LONG")
                total_liq_dist = live_entry - liq_price
                sl_dist = live_entry - sl
                safe_clearance = (sl > liq_price) and (sl_dist <= total_liq_dist * 0.60)
                active_checklist["Liquidation Buffer (SL >= 40% Above Liq)"] = safe_clearance
            else:
                sl = swing_high + (0.5 * atr)
                risk_distance = sl - live_entry
                tp = live_entry - max(2.5 * risk_distance, 2.5 * atr)
                liq_price = calculate_liquidation_price(live_entry, leverage, "SHORT")
                total_liq_dist = liq_price - live_entry
                sl_dist = sl - live_entry
                safe_clearance = (sl < liq_price) and (sl_dist <= total_liq_dist * 0.60)
                active_checklist["Liquidation Buffer (SL >= 40% Below Liq)"] = safe_clearance

            base_passed = all([v for k, v in active_checklist.items() if ("MACD" not in k or not is_high_risk_macd)])
            
            if base_passed:
                position_notional = allocated_margin * leverage
                pct_price_move = abs(tp - live_entry) / live_entry
                commission = position_notional * (COINDCX_TAKER_FEE * 2)
                gross_profit = position_notional * pct_price_move
                net_profit = gross_profit - commission
                net_roi = net_profit / allocated_margin
                total_account_growth = net_profit / capital

                if not ltf_aligned:
                    print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> ⚠️ {direction} DETECTED BUT BLOCKED (1h/30m is declining against it)")
                    continue

                if net_roi >= MIN_PROFIT_ROI:
                    status_tag = "HIGH-RISK" if is_high_risk_macd else "APPROVED"
                    print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> 🎯 {direction} SIGNAL DETECTED [{status_tag}] (ROI: {round(net_roi * 100, 2)}%)")

                    candidate_trades.append({
                        "Coin Pair": clean_pair,
                        "Timeframe": tf,
                        "Direction": direction,
                        "Entry Price": f"${round(live_entry, 4)}",
                        "Margin to Enter": f"${round(allocated_margin, 2)} USDT ({int(RISK_PER_TRADE*100)}% of Wallet)",
                        "Leverage": f"{leverage}x",
                        "Take Profit": f"${round(tp, 4)}",
                        "Stop Loss": f"${round(sl, 4)} (Dynamic Swing)",
                        "Est. Liquidation": f"${round(liq_price, 4)}",
                        "CoinDCX Fee Est.": f"${round(commission, 4)} USDT",
                        "Expected Net Profit": f"${round(net_profit, 2)} USDT",
                        "Trade Net ROI": f"{round(net_roi * 100, 2)}%",
                        "Total Account Growth": f"{round(total_account_growth * 100, 2)}%",
                        "roi_num": net_roi,
                        "auto_trade": not is_high_risk_macd,
                        "warning": "This trade has high risk as MACD check failed. Taking trade is at your own risk." if is_high_risk_macd else None
                    })
                else:
                    print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> NEUTRAL (Expected ROI {round(net_roi*100, 1)}% < Minimum 20.0%)")
            else:
                failed = [k.replace(" (Trend Alignment)", "").replace(" (Non-Choppy Market)", "").replace(" (50 & 200 EMA)", "").replace(" (< 50 EMA)", "") for k, v in active_checklist.items() if not v]
                print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> NEUTRAL ({', '.join(failed)})")
        else:
            checklist = long_checklist
            failed = [k.replace(" (Trend Alignment)", "").replace(" (Non-Choppy Market)", "").replace(" (50 & 200 EMA)", "").replace(" (< 50 EMA)", "") for k, v in checklist.items() if not v]
            print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> NEUTRAL ({', '.join(failed)})")

    return candidate_trades

def get_user_inputs():
    current_time = datetime.now().strftime("%A, %d %B %Y | %I:%M:%S %p")
    print("=======================================================")
    print("         COMPLETE MULTI-TIMEFRAME COIN SCANNER         ")
    print(f" Current Local Time: {current_time}")
    print("=======================================================")

    raw_coin = input("\nEnter Coin Symbol (e.g. TRX, XRP, SOL, BTC): ").strip().upper()
    if not raw_coin:
        print("Coin symbol cannot be empty.")
        sys.exit(1)

    clean_symbol = raw_coin.replace("B-", "").replace("_USDT", "").replace("USDT", "")
    pair_name = f"B-{clean_symbol}_USDT"

    while True:
        bal_input = input("Enter current trading wallet balance in USDT [Default: 20]: ").strip()
        if not bal_input:
            balance = 20.0
            break
        try:
            balance = float(bal_input)
            if balance > 0:
                break
            print("Please enter a positive numeric balance.")
        except ValueError:
            print("Invalid numeric value. Try again.")

    return pair_name, clean_symbol, balance

def main():
    pair_name, clean_symbol, balance = get_user_inputs()

    print(f"\nAnalyzing {clean_symbol} across 30m, 1h, 4h, 8h, and 1w (Minimum ROI: 20%)...")
    print("Checking BTC & Coin Macro Regime Filters (1D)...")
    btc_trend = get_btc_macro_trend()
    coin_trend = get_coin_macro_trend(pair_name)
    print(f"BTC  1D Market Status: [{btc_trend}]")
    print(f"{clean_symbol.ljust(4)} 1D Market Status: [{coin_trend}]\n")

    candidates = evaluate_complete_pair(pair_name, balance, btc_trend)

    if candidates:
        best_setup = max(candidates, key=lambda x: x["roi_num"])
        
        print("\n==========================================================")
        if best_setup.get("auto_trade", True):
            print("             🎯 APPROVED TRADE SETUP SIGNALS              ")
        else:
            print("          ⚠️  HIGH RISK MANUAL TRADE SUGGESTIONS ⚠️       ")
        print("==========================================================")
        print("----------------------------------------------------------")
        if not best_setup.get("auto_trade", True):
            print(f"⚠️  WARNING: {best_setup.get('warning')}\n")
        print(f"Coin Pair        : {best_setup['Coin Pair']} ({best_setup['Timeframe']})")
        print(f"Direction        : {best_setup['Direction']}")
        print(f"Entry Price      : {best_setup['Entry Price']}")
        print(f"Suggested Margin : {best_setup['Margin to Enter']}")
        print(f"Suggested Lev    : {best_setup['Leverage']}")
        print(f"Take Profit      : {best_setup['Take Profit']}")
        print(f"Stop Loss        : {best_setup['Stop Loss']}")
        print(f"Est. Liquidation : {best_setup.get('Est. Liquidation', 'N/A')}")
        print(f"CoinDCX Fee Est. : {best_setup['CoinDCX Fee Est.']}")
        print(f"Expected Net ROI : {best_setup['Trade Net ROI']} (~{best_setup['Expected Net Profit']})")
        print(f"Account Growth   : {best_setup['Total Account Growth']}")
        status_label = "[APPROVED - ALL CRITERIA MET]" if best_setup.get("auto_trade", True) else "[MANUAL ACTION REQUIRED - AUTO-TRADE BYPASSED]"
        print(f"Status           : {status_label}")
        print("----------------------------------------------------------\n")
    else:
        print(f"\nNo trade setups currently meet minimum criteria (with confirmed LTF alignment & >=20% Net ROI) for {clean_symbol}. [NEUTRAL]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan canceled by user.")
        sys.exit(0)
