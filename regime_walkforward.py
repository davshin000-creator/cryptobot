import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# ==========================
# Data
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

def backtest(
    data,
    buy_rsi,
    sell_rsi
):

    position = False
    buy_price = 0

    trades = []
    wins = 0
    losses = 0

    for i in range(len(data)):

        price = data["close"].iloc[i]

        rsi_value = (
            data["RSI"].iloc[i]
        )

        ema50 = (
            data["EMA50"].iloc[i]
        )

        ema200 = (
            data["EMA200"].iloc[i]
        )

        # ==================
        # BUY
        # ==================

        if (

            ema50 > ema200
            and
            rsi_value < buy_rsi
            and
            not position

        ):

            position = True
            buy_price = price

        # ==================
        # SELL
        # ==================

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

    # ======================
    # Results
    # ======================

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
# Optimization
# ==========================

buy_levels = [20, 25, 30, 35]
sell_levels = [65, 70, 75]

results = []

for buy_rsi in buy_levels:

    for sell_rsi in sell_levels:

        result = backtest(

            train_df,
            buy_rsi,
            sell_rsi

        )

        results.append({

            "BUY_RSI": buy_rsi,
            "SELL_RSI": sell_rsi,
            **result

        })

# ==========================
# Best Strategy
# ==========================

results_df = pd.DataFrame(
    results
)

results_df = results_df.sort_values(
    by="profit",
    ascending=False
)

best = results_df.iloc[0]

best_buy = int(
    best["BUY_RSI"]
)

best_sell = int(
    best["SELL_RSI"]
)

print(
    "\n========== BEST TRAIN RESULT ==========\n"
)

print(best)

# ==========================
# Test Validation
# ==========================

test_result = backtest(

    test_df,
    best_buy,
    best_sell

)

print(
    "\n========== TEST RESULT ==========\n"
)

print(
    "BUY_RSI:",
    best_buy
)

print(
    "SELL_RSI:",
    best_sell
)

print(
    "Trades:",
    test_result["trades"]
)

print(
    "Wins:",
    test_result["wins"]
)

print(
    "Losses:",
    test_result["losses"]
)

print(
    "Win Rate:",
    test_result["win_rate"],
    "%"
)

print(
    "Profit:",
    test_result["profit"],
    "%"
)
