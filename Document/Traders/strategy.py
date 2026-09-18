import pandas as pd
from config import (
    COINS,
    TIMEFRAMES,
    RISK_PER_TRADE,
    MIN_PROFIT_ROI,
    COINDCX_TAKER_FEE,
    BTC_PAIR
)
from market_data import fetch_candles, fetch_raw_candles
from indicators import (
    calculate_all_indicators,
    get_dynamic_swing_levels,
    calculate_liquidation_price
)

def get_market_trend(pair: str, interval: str) -> str:
    if interval == "1h":
        df = fetch_raw_candles(pair, interval="1h", limit=300)
    else:
        df = fetch_candles(pair, interval)

    if df is None or len(df) < 50:
        return "NEUTRAL"

    df = calculate_all_indicators(df)
    prev_closed = df.iloc[-2]

    if prev_closed["close"] > prev_closed["ema50"] and prev_closed["close"] > prev_closed.get("ema200", prev_closed["ema50"]):
        return "BULLISH"
    elif prev_closed["close"] < prev_closed["ema50"]:
        return "BEARISH"
    return "NEUTRAL"

def get_btc_macro_trend() -> str:
    return get_market_trend(BTC_PAIR, "1d")

def log_coin_analysis(pair: str, tf: str, checklist: dict, direction: str = None, is_high_risk_macd: bool = False):
    clean_pair = pair.replace("B-", "")

    if not direction:
        failed_reasons = []
        for gate, passed in checklist.items():
            if not passed:
                clean_gate = gate.replace(" (Trend Alignment)", "").replace(" (Non-Choppy Market)", "").replace(" (50 & 200 EMA)", "").replace(" (< 50 EMA)", "")
                failed_reasons.append(clean_gate)
        fail_str = ", ".join(failed_reasons) if failed_reasons else "Failed Criteria"
        print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> NEUTRAL ({fail_str})")
    else:
        status_tag = "HIGH-RISK" if is_high_risk_macd else "APPROVED"
        print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> 🎯 {direction} SIGNAL DETECTED [{status_tag}]")

def evaluate_pair(pair: str, capital: float, btc_trend: str):
    candidate_trades = []
    allocated_margin = capital * RISK_PER_TRADE
    clean_pair = pair.replace("B-", "")

    # 1. 1D Macro Confluence Check
    df_1d = fetch_candles(pair, "1d")
    is_1d_bullish = False
    is_1d_bearish = False
    if df_1d is not None and len(df_1d) >= 100:
        df_1d = calculate_all_indicators(df_1d)
        closed_1d = df_1d.iloc[-2]
        is_1d_bullish = (closed_1d["close"] > closed_1d["ema50"]) and (closed_1d["close"] > closed_1d["ema200"])
        is_1d_bearish = (closed_1d["close"] < closed_1d["ema50"])

    # 2. 1H Execution Confirmation Gate
    df_1h = fetch_raw_candles(pair, interval="1h", limit=300)
    ltf_1h_bullish = False
    ltf_1h_bearish = False
    if df_1h is not None and len(df_1h) >= 50:
        df_1h = calculate_all_indicators(df_1h)
        bar_1h = df_1h.iloc[-2]
        ltf_1h_bullish = bar_1h["close"] > bar_1h["ema50"]
        ltf_1h_bearish = bar_1h["close"] < bar_1h["ema50"]

    for tf in TIMEFRAMES:
        df = fetch_candles(pair, tf)
        if df is None or len(df) < 50:
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
            # 1H Confluence Validation Gate
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
                    print(f"  • {clean_pair.ljust(9)} [{tf.ljust(3)}] -> ⚠️ {direction} DETECTED BUT BLOCKED (1h is declining against it)")
                    continue

                log_coin_analysis(pair, tf, active_checklist, direction, is_high_risk_macd)

                if net_roi >= MIN_PROFIT_ROI:
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
                log_coin_analysis(pair, tf, active_checklist)
        else:
            log_coin_analysis(pair, tf, long_checklist)

    return candidate_trades

def evaluate_all_markets(capital: float):
    print("Checking BTC & Coins Multi-Timeframe Status...")
    btc_trend = get_btc_macro_trend()

    for coin in COINS:
        c_clean = coin.replace("B-", "").replace("_USDT", "")
        t_1d = get_market_trend(coin, "1d")
        t_1h = get_market_trend(coin, "1h")
        print(f"  {c_clean.ljust(4)} 1D Market Status: [{t_1d.ljust(7)}] | 1H Market Status: [{t_1h}]")
    print()

    raw_candidates = []
    for coin in COINS:
        trades = evaluate_pair(coin, capital, btc_trend)
        raw_candidates.extend(trades)

    # -------------------------------------------------------------
    # COMBINED TIMEFRAME AGGREGATION: Combines (4h, 8h) if both qualify
    # -------------------------------------------------------------
    grouped_by_coin = {}
    for trade in raw_candidates:
        symbol = trade["Coin Pair"]
        if symbol not in grouped_by_coin:
            grouped_by_coin[symbol] = []
        grouped_by_coin[symbol].append(trade)

    final_candidates = []
    for symbol, setups in grouped_by_coin.items():
        best_setup = max(setups, key=lambda x: x["roi_num"]).copy()
        
        all_tfs = [s["Timeframe"] for s in setups]
        unique_tfs = []
        for tf in ["4h", "8h", "1d"]:
            if tf in all_tfs and tf not in unique_tfs:
                unique_tfs.append(tf)

        if len(unique_tfs) > 1:
            best_setup["Timeframe"] = ", ".join(unique_tfs)

        final_candidates.append(best_setup)

    final_candidates.sort(key=lambda x: x["roi_num"], reverse=True)
    return final_candidates
