import requests
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# Kraken Historical Data
# 1 hour candles
# ==========================

url = (
    "https://api.kraken.com"
    "/0/public/OHLC"
    "?pair=XBTUSD&interval=60"
)

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# ==========================
# Close Prices
# ==========================

closes = []

for candle in candles:
    closes.append(float(candle[4]))

# ==========================
# DataFrame
# ==========================

df = pd.DataFrame(
    closes,
    columns=["close"]
)

# ==========================
# Indicators
# ==========================

# RSI
rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

# EMA50
df["EMA50"] = (
    df["close"]
    .ewm(span=50)
    .mean()
)

# EMA200
df["EMA200"] = (
    df["close"]
    .ewm(span=200)
    .mean()
)

# ==========================
# Backtest Variables
# ==========================

position = False
buy_price = 0

trades = []
wins = 0
losses = 0

TAKE_PROFIT = 4.0
STOP_LOSS = -2.0

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

    # =====================
    # BUY
    # =====================

    if (
        ema50 > ema200
        and rsi_value < 40
        and not position
    ):

        position = True
        buy_price = price

        print(f"BUY @ {price}")

    # =====================
    # SELL
    # =====================

    elif position:

        current_profit = (
            (price - buy_price)
            / buy_price
        ) * 100

        sell_reason = None

        # Take profit
        if current_profit >= TAKE_PROFIT:
            sell_reason = "TAKE PROFIT"

        # Stop loss
        elif current_profit <= STOP_LOSS:
            sell_reason = "STOP LOSS"

        # Trend broken
        elif ema50 < ema200:
            sell_reason = "TREND LOST"

        # Execute sell
        if sell_reason:

            position = False

            trades.append(
                current_profit
            )

            if current_profit > 0:
                wins += 1
            else:
                losses += 1

            print(f"SELL @ {price}")
            print(
                f"Profit: "
                f"{current_profit:.2f}%"
            )
            print(
                f"Reason: "
                f"{sell_reason}"
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

print("\n========== BACKTEST ==========")

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
