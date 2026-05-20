import requests
import pandas as pd

# ==========================
# Kraken Historical Data
# 15 minute candles
# ==========================

url = (
    "https://api.kraken.com"
    "/0/public/OHLC"
    "?pair=XBTUSD&interval=15"
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
# Breakout Indicator
# ==========================

# Previous 20 candle high
df["Highest20"] = (
    df["close"]
    .rolling(20)
    .max()
    .shift(1)
)

# ==========================
# Backtest Variables
# ==========================

position = False
buy_price = 0

trades = []
wins = 0
losses = 0

TAKE_PROFIT = 2.5
STOP_LOSS = -1.0

# ==========================
# Backtest Loop
# ==========================

for i in range(len(df)):

    price = df["close"].iloc[i]
    highest20 = df["Highest20"].iloc[i]

    if pd.isna(highest20):
        continue

    # =====================
    # BUY
    # =====================

    if (
        price > highest20
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

        # Take Profit
        if current_profit >= TAKE_PROFIT:
            sell_reason = "TAKE PROFIT"

        # Stop Loss
        elif current_profit <= STOP_LOSS:
            sell_reason = "STOP LOSS"

        # Execute Sell
        if sell_reason:

            position = False

            trades.append(
                current_profit
            )

            if current_profit > 0:
                wins += 1
            else:
                losses += 1

            print(
                f"SELL @ {price}"
            )

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
    f"Win Rate: {win_rate:.2f}%"
)

print(
    f"Total Profit: "
    f"{total_profit:.2f}%"
)

print(
    f"Average Profit: "
    f"{avg_profit:.2f}%"
)
