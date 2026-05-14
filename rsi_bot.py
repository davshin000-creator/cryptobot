import requests
import pandas as pd
from ta.momentum import RSIIndicator
import os

# 🔐 Telegram
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 📩 메시지 함수
def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.get(url, params={
        "chat_id": CHAT_ID,
        "text": text
    })

# BTC 데이터 가져오기
url = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=5"

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# 종가(close)
closes = []

for candle in candles:
    closes.append(float(candle[4]))

# dataframe
df = pd.DataFrame(closes, columns=["close"])

# RSI 계산
rsi = RSIIndicator(close=df["close"], window=14)

df["RSI"] = rsi.rsi()

# 최신 RSI
latest_rsi = df["RSI"].iloc[-1]

print("Latest RSI:", latest_rsi)

# 현재 가격
current_price = closes[-1]

# 전략
if latest_rsi < 30:

    msg = f"""
🟢 BUY SIGNAL

BTC Price: ${current_price}

RSI: {latest_rsi:.2f}

Possible oversold condition
"""

    print(msg)
    send_msg(msg)

elif latest_rsi > 70:

    msg = f"""
🔴 SELL SIGNAL

BTC Price: ${current_price}

RSI: {latest_rsi:.2f}

Possible overbought condition
"""

    print(msg)
    send_msg(msg)

else:

    msg = f"""
⚪ HOLD

BTC Price: ${current_price}

RSI: {latest_rsi:.2f}
"""

    print(msg)
