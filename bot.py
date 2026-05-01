import requests
import os

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
        return float(requests.get(url).json()["data"]["amount"])
    except:
        return None

def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        return float(requests.get(url).json()["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

def gemini_price(symbol):
    try:
        url = f"https://api.gemini.com/v1/pubticker/{symbol.lower()}usd"
        return float(requests.get(url).json()["last"])
    except:
        return None

# 🔥 KuCoin 추가
def kucoin_price(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
        return float(requests.get(url).json()["data"]["price"])
    except:
        return None

def run():
    for coin, symbol in coins.items():

        try:
            prices = {
                "Coinbase": coinbase_price(symbol),
                "Gemini": gemini_price(symbol),
                "KuCoin": kucoin_price(symbol)
            }

            if coin == "bitcoin":
                prices["Kraken"] = kraken_price()

            prices = {k: v for k, v in prices.items() if v is not None}

            if len(prices) < 2:
                continue

            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)

            max_p = prices[max_ex]
            min_p = prices[min_ex]

            diff = max_p - min_p
            percent = (diff / min_p) * 100

            fee = 0.4
            net = percent - fee

            min_diff = 50
            min_percent = 0.3

            print(f"{coin} | Net: {net:.3f}% | Diff: ${diff:.2f}")

            if net > min_percent and diff > min_diff:
                send_msg(f"""
🚨 ARBITRAGE

Coin: {coin}

BUY: {min_ex} {min_p}
SELL: {max_ex} {max_p}

Diff: ${diff:.2f}
Net: {net:.3f}%
""")

        except Exception as e:
            print("error:", e)

run()
