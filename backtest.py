import requests
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# Kraken Historical Data
# ==========================

url = (
    "https://api.kraken.com"
    "/0/public/OHLC"
    "?pair=XBTUSD&interval=5"
)

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# close prices
closes = []

for candle in candles:
    closes.append(float(candle[4]))

# dataframe
df = pd.DataFrame(
    closes,
    columns=["close"]
)

# ==========================
# RSI
# ==========================

rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

# ==========================
# Backtest Variables
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

    rsi_value = df["RSI"].iloc[i]
    price = df["close"].iloc[i]

    if pd.isna(rsi_value):
        continue

    # BUY
    if rsi_value < 30 and not position:

        position = True
        buy_price = price

    # SELL
    elif rsi_value > 70 and position:

        position = False

        profit_percent = (
            (price - buy_price)
            / buy_price
        ) * 100

        trades.append(profit_percent)

        if profit_percent > 0:
            wins += 1
        else:
            losses += 1

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

print("========== BACKTEST ==========")

print("Total Trades:", total_trades)

print("Wins:", wins)
print("Losses:", losses)

print(f"Win Rate: {win_rate:.2f}%")

print(f"Total Profit: {total_profit:.2f}%")

print(
    f"Average Profit: "
    f"{avg_profit:.2f}%"
)
