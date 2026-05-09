import requests
import pandas as pd
from ta.momentum import RSIIndicator

# BTC 가격 데이터 가져오기
url = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=5"

data = requests.get(url).json()

candles = data["result"]["XXBTZUSD"]

# 종가(close) 추출
closes = []

for candle in candles:
    closes.append(float(candle[4]))

# pandas dataframe
df = pd.DataFrame(closes, columns=["close"])

# RSI 계산
rsi = RSIIndicator(close=df["close"], window=14)

df["RSI"] = rsi.rsi()

# 최신 RSI
latest_rsi = df["RSI"].iloc[-1]

print("Latest RSI:", latest_rsi)

# 전략
if latest_rsi < 30:
    print("🟢 BUY SIGNAL")

elif latest_rsi > 70:
    print("🔴 SELL SIGNAL")

else:
    print("⚪ HOLD")
