import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# ETH Data
# ==========================

df = yf.download(

    "ETH-USD",
    period="2y",
    interval="1h",
    progress=False

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

df = df.dropna()

# ==========================
# Train/Test Split
# ==========================

split_index = int(
    len(df) * 0.7
)

train_df = df.iloc[:split_index]
test_df = df.iloc[split_index:]

# ==========================
# Backtest Function
# ==========================

def backtest(data):

    position = False
    buy_price = 0

    trades = []
    wins = 0
    losses = 0

    BUY_RSI = 25
    SELL_RSI = 80

    for i in range(len(data)):

        rsi_value = (
            data["RSI"].iloc[i]
        )

        price = (
            data["close"].iloc[i]
        )

        # ==================
        # BUY
        # ==================

        if (

            rsi_value < BUY_RSI
            and
            not position

        ):

            position = True
            buy_price = price

        # ==================
        # SELL
        # ==================

        elif (

            rsi_value > SELL_RSI
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

    total_trades = len(trades)

    total_profit = sum(trades)

    win_rate = (

        wins / total_trades * 100

        if total_trades > 0
        else 0

    )

    return {

        "trades": total_trades,

        "wins": wins,

        "losses": losses,

        "win_rate": round(
            win_rate,
            2
        ),

        "profit": round(
            total_profit,
            2
        )

    }

# ==========================
# Train Result
# ==========================

train_result = backtest(
    train_df
)

print(
    "\n========== TRAIN RESULT ==========\n"
)

print(train_result)

# ==========================
# Test Result
# ==========================

test_result = backtest(
    test_df
)

print(
    "\n========== TEST RESULT ==========\n"
)

print(test_result)
