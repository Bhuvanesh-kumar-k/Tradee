import sys
from datetime import datetime

from config import RISK_PER_TRADE, MIN_PROFIT_ROI, BTC_PAIR
from strategy import evaluate_pair, get_btc_macro_trend

def get_user_inputs():
    current_time = datetime.now().strftime("%A, %d %B %Y | %I:%M:%S %p")
    print("=======================================================")
    print("           SINGLE COIN ON-DEMAND SCANNER              ")
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
            print("Invalid number. Try again.")

    return pair_name, clean_symbol, balance

def main():
    pair_name, clean_symbol, balance = get_user_inputs()

    print(f"\nAnalyzing {clean_symbol} across 4h, 8h, and 1d...")
    print("Checking BTC Macro Regime Filter (1D)...")
    btc_trend = get_btc_macro_trend()
    print(f"BTC 1D Market Status: [{btc_trend}]\n")

    candidates = evaluate_pair(pair_name, balance, btc_trend)

    if candidates:
        best_setup = max(candidates, key=lambda x: x["roi_num"])
        
        print("\n" + "=" * 58)
        if best_setup.get("auto_trade", True):
            print("         🎯 TRADE QUALIFIED - SETUP DETAILS           ")
        else:
            print("       ⚠️  HIGH RISK SETUP (MACD FAILED) ⚠️           ")
        print("=" * 58)
        
        if not best_setup.get("auto_trade", True):
            print(f"⚠️  WARNING: {best_setup.get('warning')}\n")

        print(f"Coin Pair        : {best_setup['Coin Pair']} ({best_setup['Timeframe']})")
        print(f"Direction        : {best_setup['Direction']}")
        print(f"Entry Price      : {best_setup['Entry Price']}")
        print(f"Suggested Margin : {best_setup['Margin to Enter']}")
        print(f"Leverage         : {best_setup['Leverage']}")
        print(f"Take Profit      : {best_setup['Take Profit']}")
        print(f"Stop Loss        : {best_setup['Stop Loss']}")
        print(f"Est. Liquidation : {best_setup.get('Est. Liquidation', 'N/A')}")
        print(f"CoinDCX Fee Est. : {best_setup['CoinDCX Fee Est.']}")
        print(f"Expected Net ROI : {best_setup['Trade Net ROI']} (~{best_setup['Expected Net Profit']})")
        print(f"Account Growth   : {best_setup['Total Account Growth']}")
        print("=" * 58 + "\n")
    else:
        print(f"\nSummary for {clean_symbol}: No approved setups found across 4h, 8h, or 1d. [NEUTRAL]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan canceled by user.")
        sys.exit(0)
