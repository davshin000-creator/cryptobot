import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# Long-term BTC Data
# ==========================

df = yf.download(
    "BTC-USD",
    period="2y",
    interval="1h"
)

df = df.dropna()

# yfinance column 정리
df["close"] = df["Close"]

# ==========================
# Indicators
# ==========================

rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

df["EMA50"] = df["close"].ewm(span=50).mean()
df["EMA200"] = df["close"].ewm(span=200).mean()

# ==========================
# Backtest Variables
# ==========================

position = False
buy_price = 0
peak_price = 0

trades = []
wins = 0
losses = 0

STOP_LOSS = -0.8
TRAILING_STOP = 2.0

# ==========================
# Backtest Loop
# ==========================

for i in range(len(df)):

    price = df["close"].iloc[i]
    rsi_value = df["RSI"].iloc[i]
    ema50 = df["EMA50"].iloc[i]
    ema200 = df["EMA200"].iloc[i]

    if pd.isna(rsi_value):
        continue

    # BUY
    if (
        ema50 > ema200
        and rsi_value < 35
        and not position
    ):
        position = True
        buy_price = price
        peak_price = price

        print(f"BUY @ {price}")

    # MANAGE POSITION
    elif position:

        if price > peak_price:
            peak_price = price

        current_profit = ((price - buy_price) / buy_price) * 100
        drawdown = ((peak_price - price) / peak_price) * 100

        sell_reason = None

        if current_profit <= STOP_LOSS:
            sell_reason = "STOP LOSS"

        elif ema50 < ema200:
            sell_reason = "TREND LOST"

        elif drawdown >= TRAILING_STOP:
            sell_reason = "TRAILING STOP"

        if sell_reason:
            position = False
            trades.append(current_profit)

            if current_profit > 0:
                wins += 1
            else:
                losses += 1

            print(f"SELL @ {price}")
            print(f"Profit: {current_profit:.2f}%")
            print(f"Reason: {sell_reason}")

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

print("\n========== LONG BACKTEST ==========")
print("Total Trades:", total_trades)
print("Wins:", wins)
print("Losses:", losses)
print(f"Win Rate: {win_rate:.2f}%")
print(f"Total Profit: {total_profit:.2f}%")
print(f"Average Profit: {avg_profit:.2f}%")
