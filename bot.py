import requests
import os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 📩 텔레그램
def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram error:", e)

# 💰 Coinbase
def coinbase_price():
    try:
        url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        return None

# 💰 Kraken
def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

# 💰 Gemini
def gemini_price():
    try:
        url = "https://api.gemini.com/v1/pubticker/btcusd"
        data = requests.get(url).json()
        return float(data["last"])
    except:
        return None

def run():
    try:
        prices = {
            "Coinbase": coinbase_price(),
            "Kraken": kraken_price(),
            "Gemini": gemini_price()
        }

        # None 제거
        prices = {k: v for k, v in prices.items() if v is not None}

        print("Prices:", prices)

        if len(prices) < 2:
            print("데이터 부족")
            return

        max_exchange = max(prices, key=prices.get)
        min_exchange = min(prices, key=prices.get)

        max_price = prices[max_exchange]
        min_price = prices[min_exchange]

        diff = max_price - min_price
        percent = (diff / min_price) * 100

        print(f"MAX: {max_exchange} {max_price}")
        print(f"MIN: {min_exchange} {min_price}")
        print(f"DIFF: {diff} ({percent:.4f}%)")

        # 💰 현실 수익 필터
        fee = 0.4
        net = percent - fee

        if net > 0.2:
            send_msg(f"""
🚨 REAL ARBITRAGE

BUY: {min_exchange} {min_price}
SELL: {max_exchange} {max_price}

Gross: {percent:.4f}%
Net: {net:.4f}%
""")

    except Exception as e:
        print("error:", e)

run()
