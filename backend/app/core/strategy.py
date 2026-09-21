import pandas as pd
import numpy as np
from app.core.config import settings
from app.core.market_data import fetch_candles, fetch_raw_candles
from app.core.indicators import (
    calculate_all_indicators,
    get_dynamic_swing_levels,
    calculate_liquidation_price
)
from app.schemas.scanner import TimeframeCheckDetail


async def get_market_trend(pair: str, interval: str) -> str:
    """Get market trend for a pair and interval"""
    if interval == "1h":
        df = await fetch_raw_candles(pair, interval="1h", limit=300)
    else:
        df = await fetch_candles(pair, interval)

    if df is None or len(df) < 50:
        return "NEUTRAL"

    df = calculate_all_indicators(df)
    prev_closed = df.iloc[-2]

    if prev_closed["close"] > prev_closed["ema50"] and prev_closed["close"] > prev_closed.get("ema200", prev_closed["ema50"]):
        return "BULLISH"
    elif prev_closed["close"] < prev_closed["ema50"]:
        return "BEARISH"
    return "NEUTRAL"


async def get_btc_macro_trend() -> str:
    """Get BTC 1D macro trend for regime filter"""
    return await get_market_trend(settings.BTC_PAIR, "1d")


async def evaluate_pair_diagnostics(pair: str, capital: float, btc_trend: str, user_timeframes: list = None):
    """Evaluate a single trading pair across multiple timeframes with full diagnostics"""
    if user_timeframes is None:
        user_timeframes = ["4h", "8h", "1d"]
    
    clean_pair = pair.replace("B-", "")
    risk_per_trade = settings.DEFAULT_RISK_PER_TRADE
    allocated_margin = capital * risk_per_trade

    # 1. 1D Macro Confluence Check
    df_1d = await fetch_candles(pair, "1d")
    is_1d_bullish = False
    is_1d_bearish = False
    macro_1d_status = "NEUTRAL"
    if df_1d is not None and len(df_1d) >= 50:
        df_1d = calculate_all_indicators(df_1d)
        closed_1d = df_1d.iloc[-2]
        is_1d_bullish = (closed_1d["close"] > closed_1d["ema50"]) and (closed_1d["close"] > closed_1d.get("ema200", closed_1d["ema50"]))
        is_1d_bearish = (closed_1d["close"] < closed_1d["ema50"])
        macro_1d_status = "BULLISH" if is_1d_bullish else ("BEARISH" if is_1d_bearish else "NEUTRAL")

    # 2. 1H Execution Confirmation Gate
    df_1h = await fetch_raw_candles(pair, interval="1h", limit=300)
    ltf_1h_bullish = False
    ltf_1h_bearish = False
    ltf_1h_status = "NEUTRAL"
    if df_1h is not None and len(df_1h) >= 50:
        df_1h = calculate_all_indicators(df_1h)
        bar_1h = df_1h.iloc[-2]
        ltf_1h_bullish = bar_1h["close"] > bar_1h["ema50"]
        ltf_1h_bearish = bar_1h["close"] < bar_1h["ema50"]
        ltf_1h_status = "BULLISH" if ltf_1h_bullish else ("BEARISH" if ltf_1h_bearish else "NEUTRAL")

    timeframe_details = []
    candidate_trades = []

    for tf in user_timeframes:
        df = await fetch_candles(pair, tf)
        if df is None or len(df) < 50:
            timeframe_details.append(TimeframeCheckDetail(
                timeframe=tf,
                direction="NEUTRAL",
                is_setup_valid=False,
                failed_checks=["Insufficient historical bars for calculation"],
                passed_checks=[]
            ))
            continue

        df = calculate_all_indicators(df)
        closed_bar = df.iloc[-2]
        prior_closed_bar = df.iloc[-3]
        live_entry = float(df.iloc[-1]["close"])
        atr = closed_bar["atr"]

        swing_low, swing_high = get_dynamic_swing_levels(df, live_entry, atr)
        volatility_ratio = atr / live_entry
        leverage = 8 if volatility_ratio < 0.025 else 5

        long_checklist = {
            "BTC Macro Trend Bullish": (pair == settings.BTC_PAIR or btc_trend == "BULLISH"),
            "1D Trend Confluence (EMA50 & EMA200)": is_1d_bullish,
            "Price > EMA50 (Trend Alignment)": closed_bar["close"] > closed_bar["ema50"],
            "ADX >= 20 (Non-Choppy Trend)": closed_bar["adx"] >= 20.0,
            "RSI in Pullback Zone (40-60)": (40 <= closed_bar["rsi"] <= 60),
            "MACD Momentum Positive": (closed_bar["macdhist"] > 0 and closed_bar["macdhist"] > prior_closed_bar["macdhist"]),
            "Volume Support (>=80% SMA20)": closed_bar["volume"] >= (closed_bar["vol_sma20"] * 0.80),
            "1H LTF Alignment": ltf_1h_bullish
        }

        short_checklist = {
            "BTC Macro Trend Bearish": (pair == settings.BTC_PAIR or btc_trend == "BEARISH"),
            "1D Trend Confluence (< EMA50)": is_1d_bearish,
            "Price < EMA50 (Trend Alignment)": closed_bar["close"] < closed_bar["ema50"],
            "ADX >= 20 (Non-Choppy Trend)": closed_bar["adx"] >= 20.0,
            "RSI in Breakdown Zone (40-62)": (40 <= closed_bar["rsi"] <= 62),
            "MACD Momentum Negative": (closed_bar["macdhist"] < 0 and closed_bar["macdhist"] < prior_closed_bar["macdhist"]),
            "Volume Support (>=80% SMA20)": closed_bar["volume"] >= (closed_bar["vol_sma20"] * 0.80),
            "1H LTF Alignment": ltf_1h_bearish
        }

        # Check Long setup
        passed_long = [k for k, v in long_checklist.items() if v]
        failed_long = [k for k, v in long_checklist.items() if not v]

        # Check Short setup
        passed_short = [k for k, v in short_checklist.items() if v]
        failed_short = [k for k, v in short_checklist.items() if not v]

        direction = "NEUTRAL"
        active_checklist = {}
        passed_checks = []
        failed_checks = []
        is_setup_valid = False
        roi = None
        tp = None
        sl = None

        if len(failed_long) == 0 or (len(failed_long) == 1 and "MACD" in failed_long[0]):
            direction = "LONG"
            active_checklist = long_checklist
            passed_checks = passed_long
            failed_checks = failed_long
            sl = swing_low - (0.5 * atr)
            risk_dist = live_entry - sl
            tp = live_entry + max(2.5 * risk_dist, 2.5 * atr)
            liq_price = calculate_liquidation_price(live_entry, leverage, "LONG")
            safe_liq = (sl > liq_price) and ((live_entry - sl) <= (live_entry - liq_price) * 0.60)
            active_checklist["Liquidation Buffer (SL >= 40% Above Liq)"] = safe_liq
            if safe_liq:
                passed_checks.append("Liquidation Buffer (Safe)")
            else:
                failed_checks.append("Liquidation Buffer (Too close to liquidation)")

            pct_move = abs(tp - live_entry) / live_entry
            net_profit = (allocated_margin * leverage * pct_move) - (allocated_margin * leverage * settings.COINDCX_TAKER_FEE * 2)
            roi = net_profit / allocated_margin
            if roi >= settings.MIN_PROFIT_ROI and safe_liq:
                is_setup_valid = True

        elif len(failed_short) == 0 or (len(failed_short) == 1 and "MACD" in failed_short[0]):
            direction = "SHORT"
            active_checklist = short_checklist
            passed_checks = passed_short
            failed_checks = failed_short
            sl = swing_high + (0.5 * atr)
            risk_dist = sl - live_entry
            tp = live_entry - max(2.5 * risk_dist, 2.5 * atr)
            liq_price = calculate_liquidation_price(live_entry, leverage, "SHORT")
            safe_liq = (sl < liq_price) and ((sl - live_entry) <= (liq_price - live_entry) * 0.60)
            active_checklist["Liquidation Buffer (SL >= 40% Below Liq)"] = safe_liq
            if safe_liq:
                passed_checks.append("Liquidation Buffer (Safe)")
            else:
                failed_checks.append("Liquidation Buffer (Too close to liquidation)")

            pct_move = abs(live_entry - tp) / live_entry
            net_profit = (allocated_margin * leverage * pct_move) - (allocated_margin * leverage * settings.COINDCX_TAKER_FEE * 2)
            roi = net_profit / allocated_margin
            if roi >= settings.MIN_PROFIT_ROI and safe_liq:
                is_setup_valid = True

        else:
            # Pick whichever had more passed checks to display diagnostics
            if len(passed_long) >= len(passed_short):
                direction = "NEUTRAL"
                active_checklist = long_checklist
                passed_checks = passed_long
                failed_checks = failed_long
            else:
                direction = "NEUTRAL"
                active_checklist = short_checklist
                passed_checks = passed_short
                failed_checks = failed_short

        detail = TimeframeCheckDetail(
            timeframe=tf,
            direction=direction,
            is_setup_valid=is_setup_valid,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            checklist=active_checklist,
            roi=roi,
            entry=live_entry,
            tp=tp,
            sl=sl,
            leverage=leverage
        )
        timeframe_details.append(detail)
        if is_setup_valid:
            candidate_trades.append(detail)

    return {
        "coin_pair": clean_pair,
        "macro_1d_trend": macro_1d_status,
        "ltf_1h_trend": ltf_1h_status,
        "btc_macro_trend": btc_trend,
        "timeframe_details": timeframe_details,
        "candidate_trades": candidate_trades
    }


async def evaluate_pair(pair: str, capital: float, btc_trend: str, user_timeframes: list = None):
    """Evaluate a single trading pair across multiple timeframes with full diagnostics"""
    if user_timeframes is None:
        user_timeframes = settings.DEFAULT_TIMEFRAMES
    
    candidate_trades = []
    risk_per_trade = settings.DEFAULT_RISK_PER_TRADE
    allocated_margin = capital * risk_per_trade
    clean_pair = pair.replace("B-", "")

    # 1. 1D Macro Confluence Check
    df_1d = await fetch_candles(pair, "1d")
    is_1d_bullish = False
    is_1d_bearish = False
    macro_1d_status = "NEUTRAL"
    if df_1d is not None and len(df_1d) >= 100:
        df_1d = calculate_all_indicators(df_1d)
        closed_1d = df_1d.iloc[-2]
        is_1d_bullish = (closed_1d["close"] > closed_1d["ema50"]) and (closed_1d["close"] > closed_1d["ema200"])
        is_1d_bearish = (closed_1d["close"] < closed_1d["ema50"])
        macro_1d_status = "BULLISH" if is_1d_bullish else ("BEARISH" if is_1d_bearish else "NEUTRAL")

    # 2. 1H Execution Confirmation Gate
    df_1h = await fetch_raw_candles(pair, interval="1h", limit=300)
    ltf_1h_bullish = False
    ltf_1h_bearish = False
    ltf_1h_status = "NEUTRAL"
    if df_1h is not None and len(df_1h) >= 50:
        df_1h = calculate_all_indicators(df_1h)
        bar_1h = df_1h.iloc[-2]
        ltf_1h_bullish = bar_1h["close"] > bar_1h["ema50"]
        ltf_1h_bearish = bar_1h["close"] < bar_1h["ema50"]
        ltf_1h_status = "BULLISH" if ltf_1h_bullish else ("BEARISH" if ltf_1h_bearish else "NEUTRAL")

    # 3. Collect timeframe details for all timeframes
    timeframe_details = []

    for tf in user_timeframes:
        df = await fetch_candles(pair, tf)
        if df is None or len(df) < 50:
            timeframe_details.append({
                "timeframe": tf,
                "direction": "NEUTRAL",
                "is_setup_valid": False,
                "passed_checks": [],
                "failed_checks": ["Insufficient data"],
                "checklist": {},
                "roi": None,
                "entry": None,
                "tp": None,
                "sl": None,
                "leverage": None
            })
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
        passed_checks = []
        failed_checks = []

        long_checklist = {
            "BTC Macro Trend Bullish": (pair == settings.BTC_PAIR or btc_trend == "BULLISH"),
            "1D Trend Confluence (50 & 200 EMA)": is_1d_bullish,
            "Price > EMA50 (Trend Alignment)": closed_bar["close"] > closed_bar["ema50"],
            "ADX >= 20 (Non-Choppy Market)": closed_bar["adx"] >= 20.0,
            "RSI in Pullback Zone (40-60)": (40 <= closed_bar["rsi"] <= 60),
            "MACD Momentum Positive": (closed_bar["macdhist"] > 0 and closed_bar["macdhist"] > prior_closed_bar["macdhist"]),
            "Volume Support (>=80% SMA20)": closed_bar["volume"] >= (closed_bar["vol_sma20"] * 0.80)
        }

        short_checklist = {
            "BTC Macro Trend Bearish": (pair == settings.BTC_PAIR or btc_trend == "BEARISH"),
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
            # Build failed checks from whichever checklist has more passes
            long_passes = sum(long_checklist.values())
            short_passes = sum(short_checklist.values())
            if long_passes >= short_passes:
                active_checklist = long_checklist
                direction = "LONG" if long_passes > 0 else "NEUTRAL"
            else:
                active_checklist = short_checklist
                direction = "SHORT" if short_passes > 0 else "NEUTRAL"

        # Build passed/failed checks
        if active_checklist:
            for check, passed in active_checklist.items():
                if passed:
                    passed_checks.append(check)
                else:
                    failed_checks.append(check)

        is_setup_valid = False
        if direction and direction != "NEUTRAL":
            # 1H Confluence Validation Gate
            ltf_aligned = True
            if tf in ["4h", "8h"]:
                if direction == "LONG" and not ltf_1h_bullish:
                    ltf_aligned = False
                    failed_checks.append("1H Trend Alignment")
                elif direction == "SHORT" and not ltf_1h_bearish:
                    ltf_aligned = False
                    failed_checks.append("1H Trend Alignment")

            if direction == "LONG":
                sl = swing_low - (0.5 * atr)
                risk_distance = live_entry - sl
                tp = live_entry + max(2.5 * risk_distance, 2.5 * atr)
                liq_price = calculate_liquidation_price(live_entry, leverage, "LONG")
                total_liq_dist = live_entry - liq_price
                sl_dist = live_entry - sl
                safe_clearance = (sl > liq_price) and (sl_dist <= total_liq_dist * 0.60)
                active_checklist["Liquidation Buffer (SL >= 40% Above Liq)"] = safe_clearance
                if not safe_clearance:
                    failed_checks.append("Liquidation Buffer (SL >= 40% Above Liq)")
                else:
                    passed_checks.append("Liquidation Buffer (SL >= 40% Above Liq)")
            else:
                sl = swing_high + (0.5 * atr)
                risk_distance = sl - live_entry
                tp = live_entry - max(2.5 * risk_distance, 2.5 * atr)
                liq_price = calculate_liquidation_price(live_entry, leverage, "SHORT")
                total_liq_dist = liq_price - live_entry
                sl_dist = sl - live_entry
                safe_clearance = (sl < liq_price) and (sl_dist <= total_liq_dist * 0.60)
                active_checklist["Liquidation Buffer (SL >= 40% Below Liq)"] = safe_clearance
                if not safe_clearance:
                    failed_checks.append("Liquidation Buffer (SL >= 40% Below Liq)")
                else:
                    passed_checks.append("Liquidation Buffer (SL >= 40% Below Liq)")

            base_passed = all([v for k, v in active_checklist.items() if ("MACD" not in k or not is_high_risk_macd)])
            
            if base_passed and ltf_aligned:
                position_notional = allocated_margin * leverage
                pct_price_move = abs(tp - live_entry) / live_entry
                commission = position_notional * (settings.COINDCX_TAKER_FEE * 2)
                gross_profit = position_notional * pct_price_move
                net_profit = gross_profit - commission
                net_roi = net_profit / allocated_margin
                total_account_growth = net_profit / capital

                if net_roi >= settings.MIN_PROFIT_ROI:
                    is_setup_valid = True
                    candidate_trades.append({
                        "Coin Pair": clean_pair,
                        "Timeframe": tf,
                        "Direction": direction,
                        "Entry Price": live_entry,
                        "Margin to Enter": allocated_margin,
                        "Leverage": leverage,
                        "Take Profit": tp,
                        "Stop Loss": sl,
                        "Est. Liquidation": liq_price,
                        "CoinDCX Fee Est.": commission,
                        "Expected Net Profit": net_profit,
                        "Trade Net ROI": net_roi,
                        "Total Account Growth": total_account_growth,
                        "roi_num": net_roi,
                        "auto_trade": not is_high_risk_macd,
                        "warning": "This trade has high risk as MACD check failed." if is_high_risk_macd else None,
                        "checklist": active_checklist,
                        "indicator_values": {
                            "ema20": closed_bar["ema20"],
                            "ema50": closed_bar["ema50"],
                            "ema200": closed_bar.get("ema200"),
                            "rsi": closed_bar["rsi"],
                            "macd_hist": closed_bar["macdhist"],
                            "adx": closed_bar["adx"],
                            "atr": atr
                        }
                    })
                else:
                    failed_checks.append(f"Net ROI >= {settings.MIN_PROFIT_ROI * 100}%")

        timeframe_details.append({
            "timeframe": tf,
            "direction": direction if direction else "NEUTRAL",
            "is_setup_valid": is_setup_valid,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "checklist": active_checklist or {},
            "roi": net_roi if is_setup_valid else None,
            "entry": live_entry if is_setup_valid else None,
            "tp": tp if is_setup_valid else None,
            "sl": sl if is_setup_valid else None,
            "leverage": leverage if is_setup_valid else None
        })

    return {
        "coin_pair": clean_pair,
        "macro_1d": macro_1d_status,
        "ltf_1h": ltf_1h_status,
        "btc_macro": btc_trend,
        "timeframe_details": timeframe_details,
        "candidate_trades": candidate_trades
    }


async def evaluate_all_markets(capital: float, coins: list = None, user_timeframes: list = None):
    """Evaluate all markets and aggregate results"""
    if coins is None:
        coins = settings.DEFAULT_COINS
    
    btc_trend = await get_btc_macro_trend()

    raw_candidates = []
    for coin in coins:
        trades = await evaluate_pair(coin, capital, btc_trend, user_timeframes)
        raw_candidates.extend(trades)

    # Grouped Timeframe Aggregation
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
