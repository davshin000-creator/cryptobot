import requests
import pandas as pd
from ta.momentum import RSIIndicator
import os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 📩 Telegram
def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.get(url, params={
        "chat_id": CHAT_ID,
        "text": text
    })

# BTC 데이터
url = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=5"

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# 종가 추출
closes = []

for candle in candles:
    closes.append(float(candle[4]))

# dataframe
df = pd.DataFrame(closes, columns=["close"])

# RSI 계산
rsi = RSIIndicator(close=df["close"], window=14)

df["RSI"] = rsi.rsi()

latest_rsi = df["RSI"].iloc[-1]

current_price = closes[-1]

print("RSI:", latest_rsi)
print("Price:", current_price)

# =========================
# PAPER TRADING
# =========================

# 가상 상태
position = False
buy_price = 0

# BUY
if latest_rsi < 30 and not position:

    position = True
    buy_price = current_price

    msg = f"""
🟢 PAPER BUY

BTC: ${current_price}

RSI: {latest_rsi:.2f}
"""

    print(msg)
    send_msg(msg)

# SELL
elif latest_rsi > 70 and position:

    position = False

    profit_percent = (
        (current_price - buy_price)
        / buy_price
    ) * 100

    msg = f"""
🔴 PAPER SELL

Buy Price: ${buy_price}
Sell Price: ${current_price}

Profit: {profit_percent:.2f}%
"""

    print(msg)
    send_msg(msg)

# HOLD
else:

    print("⚪ HOLD")
