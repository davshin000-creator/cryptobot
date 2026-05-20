import requests
import pandas as pd
from ta.momentum import RSIIndicator
import os
import csv
import json

# ==========================
# Telegram Secrets
# ==========================

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ==========================
# Telegram Message
# ==========================

def send_msg(text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.get(
        url,
        params={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

# ==========================
# Trade Log CSV
# ==========================

def save_trade(action, price, rsi, profit=""):

    with open(
        "trade_log.csv",
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            action,
            price,
            round(rsi, 2),
            profit
        ])

# ==========================
# Position Save (memory)
# ==========================

STATE_FILE = "state.json"


def load_state():

    try:
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    except:
        return {
            "position": False,
            "buy_price": 0
        }


def save_state(position, buy_price):

    with open(STATE_FILE, "w") as file:

        json.dump({
            "position": position,
            "buy_price": buy_price
        }, file)

# ==========================
# Kraken BTC Data
# ==========================

url = (
    "https://api.kraken.com"
    "/0/public/OHLC"
    "?pair=XBTUSD&interval=5"
)

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# close price
closes = []

for candle in candles:
    closes.append(float(candle[4]))

# ==========================
# RSI Calculation
# ==========================

df = pd.DataFrame(
    closes,
    columns=["close"]
)

rsi = RSIIndicator(
    close=df["close"],
    window=14
)

df["RSI"] = rsi.rsi()

latest_rsi = df["RSI"].iloc[-1]

current_price = closes[-1]

print("RSI:", latest_rsi)
print("Price:", current_price)

# ==========================
# Load Current Position
# ==========================

state = load_state()

position = state["position"]
buy_price = state["buy_price"]

# ==========================
# BUY SIGNAL
# ==========================

if latest_rsi < 30 and not position:

    position = True
    buy_price = current_price

    save_state(
        position,
        buy_price
    )

    save_trade(
        "BUY",
        current_price,
        latest_rsi
    )

    msg = f"""
🟢 PAPER BUY

BTC Price: ${current_price}

RSI: {latest_rsi:.2f}
"""

    print(msg)
    send_msg(msg)

# ==========================
# SELL SIGNAL
# ==========================

elif latest_rsi > 70 and position:

    position = False

    profit_percent = (
        (current_price - buy_price)
        / buy_price
    ) * 100

    save_state(
        position,
        0
    )

    save_trade(
        "SELL",
        current_price,
        latest_rsi,
        round(profit_percent, 2)
    )

    msg = f"""
🔴 PAPER SELL

Buy Price: ${buy_price}

Sell Price: ${current_price}

Profit: {profit_percent:.2f}%
"""

    print(msg)
    send_msg(msg)

# ==========================
# HOLD
# ==========================

else:

    print("⚪ HOLD")

    print(
        f"RSI: {latest_rsi:.2f}"
    )

    print(
        f"BTC: ${current_price}"
    )
