import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# BTC Data
# ==========================

df = yf.download(
    "BTC-USD",
    period="2y",
    interval="1h"
)

df = df.dropna()

df["close"] = df["Close"]

# ==========================
# RSI
# ==========================

rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

# ==========================
# Optimization
# ==========================

results = []

# RSI buy range
buy_levels = [20, 25, 30, 35, 40]

# RSI sell range
sell_levels = [55, 60, 65, 70, 75]

# ==========================
# Loop
# ==========================

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

            rsi_value = df["RSI"].iloc[i]
            price = df["close"].iloc[i]

            if pd.isna(rsi_value):
                continue

            # BUY
            if (
                rsi_value < buy_rsi
                and not position
            ):

                position = True
                buy_price = price

            # SELL
            elif (
                rsi_value > sell_rsi
                and position
            ):

                position = False

                profit = (
                    (price - buy_price)
                    / buy_price
                ) * 100

                trades.append(profit)

                if profit > 0:
                    wins += 1
                else:
                    losses += 1

        # ==================
        # Results
        # ==================

        total_trades = len(trades)

        total_profit = sum(trades)

        win_rate = (
            wins / total_trades * 100
            if total_trades > 0
            else 0
        )

        results.append({

            "BUY_RSI": buy_rsi,
            "SELL_RSI": sell_rsi,
            "TRADES": total_trades,
            "WIN_RATE": round(
                win_rate,
                2
            ),
            "PROFIT": round(
                total_profit,
                2
            )

        })

# ==========================
# Final Results
# ==========================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="PROFIT",
    ascending=False
)

print(
    "\n========== TOP RESULTS ==========\n"
)

print(
    results_df.head(10)
)
