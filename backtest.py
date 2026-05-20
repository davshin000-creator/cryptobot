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

# EMA20
df["EMA20"] = (
    df["close"]
    .ewm(span=20)
    .mean()
)

# EMA50
df["EMA50"] = (
    df["close"]
    .ewm(span=50)
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

# ==========================
# Backtest Loop
# ==========================

for i in range(len(df)):

    rsi_value = df["RSI"].iloc[i]
    ema20 = df["EMA20"].iloc[i]
    ema50 = df["EMA50"].iloc[i]
    price = df["close"].iloc[i]

    if pd.isna(rsi_value):
        continue

    # =====================
    # BUY
    # =====================

    if (
        ema20 > ema50
        and rsi_value > 55
        and not position
    ):

        position = True
        buy_price = price

        print(f"BUY @ {price}")

    # =====================
    # SELL
    # =====================

    elif (
        position
        and (
            ema20 < ema50
            or rsi_value < 45
        )
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

print("\n========== BACKTEST ==========")

print(
    "Total Trades:",
    total_trades
)

print(
    "Wins:",
    wins
)

print(
    "Losses:",
    losses
)

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
