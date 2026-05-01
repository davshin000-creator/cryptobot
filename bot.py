import requests
import os
import time

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL"
}

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except:
        pass

def coinbase_price(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        return None

def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

def gemini_price(symbol):
    try:
        url = f"https://api.gemini.com/v1/pubticker/{symbol.lower()}usd"
        data = requests.get(url).json()
        return float(data["last"])
    except:
        return None

def check_arbitrage():
    for coin, symbol in coins.items():

        try:
            if coin == "bitcoin":
                prices = {
                    "Coinbase": coinbase_price(symbol),
                    "Kraken": kraken_price(),
                    "Gemini": gemini_price(symbol)
                }
            else:
                prices = {
                    "Coinbase": coinbase_price(symbol),
                    "Gemini": gemini_price(symbol)
                }

            prices = {k: v for k, v in prices.items() if v is not None}

            if len(prices) < 2:
                continue

            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)

            max_p = prices[max_ex]
            min_p = prices[min_ex]

            diff = max_p - min_p
            percent = (diff / min_p) * 100

            # 💰 현실 필터
            fee = 0.4
            net = percent - fee

            print(f"{coin} | {net:.3f}%")

            if net > 0.25:
                send_msg(f"""
🚨 ARBITRAGE

Coin: {coin}

BUY: {min_ex} {min_p}
SELL: {max_ex} {max_p}

Net: {net:.3f}%
""")

        except:
            continue

# 🚀 초고속 루프 (핵심)
def run_once():
    check_arbitrage()

run_once()
