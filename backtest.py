import yfinance as yf
import pandas as pd

# ==========================
# BTC Long-Term Data
# ==========================

df = yf.download(
    "BTC-USD",
    period="2y",
    interval="1d"
)

df = df.dropna()

# close
df["close"] = df["Close"]

# ==========================
# SMA200
# ==========================

df["SMA200"] = (
    df["close"]
    .rolling(window=200)
    .mean()
)

# ==========================
# Variables
# ==========================

position = False
buy_price = 0

trades = []
wins = 0
losses = 0

# ==========================
# Backtest Loop
# ==========================

for i in range(len(df)):

    price = df["close"].iloc[i]
    sma200 = df["SMA200"].iloc[i]

    if pd.isna(sma200):
        continue

    # =====================
    # BUY
    # =====================

    if (
        price > sma200
        and not position
    ):

        position = True
        buy_price = price

        print(f"BUY @ {price}")

    # =====================
    # SELL
    # =====================

    elif (
        price < sma200
        and position
    ):

        position = False

        profit_percent = (
            (price - buy_price)
            / buy_price
        ) * 100

        trades.append(
            profit_percent
        )

        if profit_percent > 0:
            wins += 1
        else:
            losses += 1

        print(f"SELL @ {price}")

        print(
            f"Profit: "
            f"{profit_percent:.2f}%"
        )

# ==========================
# Results
# ==========================

total_trades = len(trades)

total_profit = sum(trades)

win_rate = (
    wins / total_trades * 100
    if total_trades > 0
    else 0
)

avg_profit = (
    total_profit / total_trades
    if total_trades > 0
    else 0
)

print("\n========== SMA200 BACKTEST ==========")

print("Total Trades:", total_trades)

print("Wins:", wins)

print("Losses:", losses)

print(
    f"Win Rate: "
    f"{win_rate:.2f}%"
)

print(
    f"Total Profit: "
    f"{total_profit:.2f}%"
)

print(
    f"Average Profit: "
    f"{avg_profit:.2f}%"
)
