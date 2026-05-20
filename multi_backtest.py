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
# Indicators
# ==========================

rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

df["EMA50"] = (
    df["close"]
    .ewm(span=50)
    .mean()
)

df["EMA200"] = (
    df["close"]
    .ewm(span=200)
    .mean()
)

# ==========================
# Strategy Tester Function
# ==========================

def run_strategy(
    name,
    buy_condition,
    sell_condition
):

    position = False
    buy_price = 0

    trades = []
    wins = 0
    losses = 0

    for i in range(len(df)):

        price = df["close"].iloc[i]

        if not position and buy_condition(i):

            position = True
            buy_price = price

        elif position and sell_condition(i):

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

    total_trades = len(trades)

    total_profit = sum(trades)

    win_rate = (
        wins / total_trades * 100
        if total_trades > 0
        else 0
    )

    print("\n====================")
    print(f"Strategy: {name}")
    print("====================")

    print(
        f"Trades: {total_trades}"
    )

    print(
        f"Win Rate: "
        f"{win_rate:.2f}%"
    )

    print(
        f"Total Profit: "
        f"{total_profit:.2f}%"
    )

# ==========================
# RSI Strategy
# ==========================

run_strategy(

    "RSI",

    lambda i:
        df["RSI"].iloc[i] < 30,

    lambda i:
        df["RSI"].iloc[i] > 70
)

# ==========================
# EMA Strategy
# ==========================

run_strategy(

    "EMA Trend",

    lambda i:
        df["EMA50"].iloc[i]
        > df["EMA200"].iloc[i],

    lambda i:
        df["EMA50"].iloc[i]
        < df["EMA200"].iloc[i]
)

# ==========================
# Pullback Strategy
# ==========================

run_strategy(

    "Pullback",

    lambda i:
        (
            df["EMA50"].iloc[i]
            > df["EMA200"].iloc[i]
        )
        and
        (
            df["RSI"].iloc[i] < 35
        ),

    lambda i:
        (
            df["RSI"].iloc[i] > 60
        )
)
