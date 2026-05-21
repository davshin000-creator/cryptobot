import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# Coins
# ==========================

coins = {
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
    "SOL-USD": "SOL"
}

# ==========================
# RSI Settings
# ==========================

buy_levels = [20, 25, 30, 35]
sell_levels = [65, 70, 75, 80]

# ==========================
# Final Results
# ==========================

final_results = []

# ==========================
# Loop Coins
# ==========================

for ticker, symbol in coins.items():

    print(f"\n===== {symbol} =====")

    # ======================
    # Download Data
    # ======================

    df = yf.download(

        ticker,
        period="6mo",
        interval="1h"

    )

    df = df.dropna()

    if len(df) < 100:
        print("Not enough data")
        continue

    df["close"] = df["Close"]

    # ======================
    # RSI
    # ======================

    rsi = RSIIndicator(

        close=df["close"],
        window=14

    )

    df["RSI"] = rsi.rsi()

    df = df.dropna()

    # ======================
    # Best Tracking
    # ======================

    best_profit = -9999
    best_buy = None
    best_sell = None
    best_winrate = 0
    best_trades = 0

    # ======================
    # Optimization Loop
    # ======================

    for buy_rsi in buy_levels:

        for sell_rsi in sell_levels:

            position = False
            buy_price = 0

            trades = []
            wins = 0
            losses = 0

            # ==================
            # Backtest
            # ==================

            for i in range(len(df)):

                rsi_value = (
                    df["RSI"].iloc[i]
                )

                price = (
                    df["close"].iloc[i]
                )

                if pd.isna(rsi_value):
                    continue

                # BUY
                if (

                    rsi_value < buy_rsi
                    and
                    not position

                ):

                    position = True
                    buy_price = price

                # SELL
                elif (

                    rsi_value > sell_rsi
                    and
                    position

                ):

                    position = False

                    profit = (
                        (price - buy_price)
                        / buy_price
                    ) * 100

                    trades.append(
                        profit
                    )

                    if profit > 0:
                        wins += 1
                    else:
                        losses += 1

            # ==================
            # Results
            # ==================

            total_profit = sum(trades)

            total_trades = len(trades)

            win_rate = (

                wins / total_trades * 100

                if total_trades > 0
                else 0

            )

            # ==================
            # Best Strategy
            # ==================

            if total_profit > best_profit:

                best_profit = total_profit

                best_buy = buy_rsi

                best_sell = sell_rsi

                best_winrate = win_rate

                best_trades = total_trades

    # ======================
    # Save Results
    # ======================

    final_results.append({

        "COIN": symbol,

        "BUY_RSI": best_buy,

        "SELL_RSI": best_sell,

        "TRADES": best_trades,

        "WIN_RATE": round(
            best_winrate,
            2
        ),

        "PROFIT": round(
            best_profit,
            2
        )

    })

# ==========================
# Final Table
# ==========================

results_df = pd.DataFrame(
    final_results
)

results_df = results_df.sort_values(
    by="PROFIT",
    ascending=False
)

print(
    "\n========== FINAL RESULTS ==========\n"
)

print(results_df)
