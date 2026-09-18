import os
import sys
import time
from datetime import datetime, timedelta

from config import COINS, RISK_PER_TRADE, COINDCX_TAKER_FEE, LOOP_INTERVAL_SECONDS
from market_data import fetch_candles, fetch_current_price
from strategy import evaluate_all_markets
from indicators import calculate_all_indicators

MAX_OPEN_TRADES = 3
AVAILABLE_TRADE_IDS = ["TR-1", "TR-2", "TR-3"]
active_trades = {}

def get_user_balance():
    while True:
        user_val = input("\nEnter current futures trading balance in USDT: ").strip()
        try:
            total_balance = float(user_val)
            if total_balance > 0:
                return total_balance
            print("Please enter a positive numeric balance.")
        except ValueError:
            print("Invalid input. Try again.")

def get_current_price(pair: str) -> float | None:
    return fetch_current_price(pair)

def evaluate_early_exit(coin: str, direction: str, timeframe: str) -> str | None:
    try:
        primary_tf = timeframe.split(",")[0].strip()
        raw_pair = f"B-{coin}_USDT" if not coin.startswith("B-") else coin
        df = fetch_candles(raw_pair, primary_tf)
        if df is None or len(df) < 50:
            return None
        df = calculate_all_indicators(df)
        closed_bar = df.iloc[-2]
        
        if direction == "LONG":
            if closed_bar["close"] < closed_bar["ema50"]:
                return "Closed bar dropped below EMA50 (Trend Broken)"
            if closed_bar["macdhist"] < 0:
                return "MACD Histogram turned negative (Bearish Momentum)"
        elif direction == "SHORT":
            if closed_bar["close"] > closed_bar["ema50"]:
                return "Closed bar surged above EMA50 (Trend Broken)"
            if closed_bar["macdhist"] > 0:
                return "MACD Histogram turned positive (Bullish Momentum)"
    except Exception:
        return None
    return None

def monitor_and_display_active_trades():
    if not active_trades:
        print("\n----------------------------------------------------------")
        print(" ACTIVE POSITIONS: 0/3 Slots In Use (No active trades)")
        print("----------------------------------------------------------")
        return

    print("\n==========================================================")
    print(f"             CURRENT OPENED TRADE STATUS ({len(active_trades)}/{MAX_OPEN_TRADES})")
    print("==========================================================")
    closed_ids = []

    for trade_id, trade in list(active_trades.items()):
        raw_pair = f"B-{trade['coin']}_USDT" if not trade['coin'].startswith("B-") else trade['coin']
        curr_price = get_current_price(raw_pair)

        if curr_price is None:
            print(f"[{trade_id} | {trade['coin']}] ⚠️ Unable to fetch live price.")
            continue

        entry = trade["entry_price"]
        direction = trade["direction"]
        leverage = trade["leverage"]
        margin = trade["margin"]
        sl = trade["sl"]
        tp = trade["tp"]
        tf = trade["timeframe"]

        if direction == "LONG":
            pct_move = (curr_price - entry) / entry
            hit_tp = curr_price >= tp
            hit_sl = curr_price <= sl
        else:
            pct_move = (entry - curr_price) / entry
            hit_tp = curr_price <= tp
            hit_sl = curr_price >= sl

        position_notional = margin * leverage
        fee = position_notional * (COINDCX_TAKER_FEE * 2)
        gross_profit = position_notional * pct_move
        net_profit = gross_profit - fee
        pnl_pct = (net_profit / margin) * 100

        print("----------------------------------------------------------")
        print(f"Trade ID         : {trade_id} [{trade['coin']}_USDT ({tf})]")
        print(f"Direction        : {direction} ({leverage}x Leverage)")
        print(f"Entry Price      : ${entry:,.4f}")
        print(f"Current Price    : ${curr_price:,.4f}")
        print(f"Margin In Use    : ${margin:,.2f} USDT")
        print(f"Current Net PnL  : {pnl_pct:+.2f}% (${net_profit:+.2f} USDT)")
        print(f"Take Profit      : ${tp:,.4f}")
        print(f"Stop Loss        : ${sl:,.4f}")

        early_warn = evaluate_early_exit(trade['coin'], direction, tf)
        if early_warn:
            print(f"Early Exit Alert : ⚠️ CLOSE RECOMMENDED - {early_warn}")
        else:
            print(f"Health Status    : ✅ Trend Intact. Maintain Position.")

        reason = None
        if hit_tp:
            reason = f"TARGET HIT (+{pnl_pct:.2f}%)"
        elif hit_sl:
            reason = f"STOP LOSS HIT ({pnl_pct:.2f}%)"

        if reason:
            print(f">>> ACTION: POSITION CLOSED ({reason}) | Realized: ${net_profit:+.2f} USDT")
            AVAILABLE_TRADE_IDS.append(trade_id)
            AVAILABLE_TRADE_IDS.sort()
            closed_ids.append(trade_id)

    print("----------------------------------------------------------\n")

    for tid in closed_ids:
        del active_trades[tid]

def process_market_candidates(candidates: list, total_balance: float):
    if not candidates:
        print("\nNo trade setups currently meet minimum criteria.")
        return

    manual_candidates = [c for c in candidates if not c.get("auto_trade", True)]
    auto_candidates = [c for c in candidates if c.get("auto_trade", True)]

    if manual_candidates:
        print("\n==========================================================")
        print("          ⚠️  HIGH RISK MANUAL TRADE SUGGESTIONS ⚠️       ")
        print("==========================================================")
        for setup in manual_candidates:
            print("----------------------------------------------------------")
            print(f"⚠️  WARNING: {setup.get('warning')}")
            print(f"Coin Pair        : {setup['Coin Pair']} ({setup['Timeframe']})")
            print(f"Direction        : {setup['Direction']}")
            print(f"Entry Price      : {setup['Entry Price']}")
            print(f"Suggested Lev    : {setup['Leverage']}")
            print(f"Take Profit      : {setup['Take Profit']}")
            print(f"Stop Loss        : {setup['Stop Loss']}")
            print(f"Est. Liquidation : {setup.get('Est. Liquidation', 'N/A')}")
            print(f"Expected Net ROI : {setup['Trade Net ROI']} (~{setup['Expected Net Profit']})")
            print("Status           : [MANUAL ACTION REQUIRED - AUTO-TRADE BYPASSED]")
            print("----------------------------------------------------------")

    if auto_candidates:
        print("\n==========================================================")
        print("             🎯 APPROVED TRADE SETUP SIGNALS              ")
        print("==========================================================")
        for setup in auto_candidates:
            print("----------------------------------------------------------")
            print(f"Coin Pair        : {setup['Coin Pair']} ({setup['Timeframe']})")
            print(f"Direction        : {setup['Direction']}")
            print(f"Entry Price      : {setup['Entry Price']}")
            print(f"Suggested Lev    : {setup['Leverage']}")
            print(f"Take Profit      : {setup['Take Profit']}")
            print(f"Stop Loss        : {setup['Stop Loss']}")
            print(f"Est. Liquidation : {setup.get('Est. Liquidation', 'N/A')}")
            print(f"Expected Net ROI : {setup['Trade Net ROI']} (~{setup['Expected Net Profit']})")
            print("Status           : [APPROVED - ALL CRITERIA MET]")
            print("----------------------------------------------------------")

        active_coins = {t["coin"] for t in active_trades.values()}
        eligible = [c for c in auto_candidates if c["Coin Pair"].split("_")[0] not in active_coins]
        eligible.sort(key=lambda x: x["roi_num"], reverse=True)

        for setup in eligible:
            if len(active_trades) >= MAX_OPEN_TRADES or not AVAILABLE_TRADE_IDS:
                break

            trade_id = AVAILABLE_TRADE_IDS.pop(0)
            coin_symbol = setup["Coin Pair"].split("_")[0]

            clean_entry = float(setup["Entry Price"].replace("$", "").replace(",", ""))
            clean_tp = float(setup["Take Profit"].replace("$", "").replace(",", ""))
            clean_sl = float(setup["Stop Loss"].split()[0].replace("$", "").replace(",", ""))
            clean_lev = int(setup["Leverage"].replace("x", ""))
            allocated_margin = total_balance * RISK_PER_TRADE

            active_trades[trade_id] = {
                "coin": coin_symbol,
                "direction": setup["Direction"],
                "entry_price": clean_entry,
                "tp": clean_tp,
                "sl": clean_sl,
                "leverage": clean_lev,
                "margin": allocated_margin,
                "timeframe": setup["Timeframe"],
                "open_time": datetime.now().strftime("%I:%M:%S %p")
            }

            print(f"\n>>> [REGISTERED SIMULATED POSITION: {trade_id} | {coin_symbol} {setup['Direction']} {clean_lev}x]\n")

def main():
    current_time = datetime.now().strftime("%A, %d %B %Y | %I:%M:%S %p")
    print("=======================================================")
    print(" Starting Persistent Trading Agent")
    print(f" Current Local Time: {current_time}")
    print("=======================================================")

    total_balance = get_user_balance()
    allocated_margin = total_balance * RISK_PER_TRADE

    print(f"\nActive Balance: ${total_balance:,.2f} USDT")
    print(f"Risk Per Trade: {int(RISK_PER_TRADE * 100)}% (${allocated_margin:,.2f} USDT margin)")
    print(f"Concurrency Capacity: Maximum {MAX_OPEN_TRADES} Simultaneous Active Trades")
    print("Agent will cycle every 5 minutes. Press Ctrl + C at any time to stop.\n")

    cycle_count = 1
    while True:
        cycle_time = datetime.now().strftime("%I:%M:%S %p")
        print(f"\n>>> [CYCLE #{cycle_count} - {cycle_time}] Checking markets...")

        try:
            print(f"Scanning high-timeframe setups (Open Slots: {MAX_OPEN_TRADES - len(active_trades)}/{MAX_OPEN_TRADES})...")
            candidates = evaluate_all_markets(total_balance)
            
            process_market_candidates(candidates, total_balance)
            monitor_and_display_active_trades()

        except Exception as e:
            print(f"⚠️ Error encountered during cycle execution: {e}")

        next_check_dt = datetime.now() + timedelta(seconds=LOOP_INTERVAL_SECONDS)
        next_check_str = next_check_dt.strftime("%I:%M:%S %p")
        print(f" {cycle_count} Cycle completed. Next check at {next_check_str}... [Press Ctrl+C to terminate]\n")
        
        cycle_count += 1
        time.sleep(LOOP_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user. Open simulated positions preserved in memory session.")
        sys.exit(0)
