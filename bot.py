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
    except Exception as e:
        print("Telegram error:", e)

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

def run():
    for coin, symbol in coins.items():

        try:
            # BTC → Kraken 포함
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

            # None 제거
            prices = {k: v for k, v in prices.items() if v is not None}

            if len(prices) < 2:
                print(f"{coin}: 데이터 부족")
                continue

            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)

            max_price = prices[max_ex]
            min_price = prices[min_ex]

            diff = max_price - min_price
            percent = (diff / min_price) * 100

            print(f"{coin} | {percent:.4f}%")

            # 💰 현실 필터
            fee = 0.4
            net = percent - fee

            if net > 0.2:
                msg = f"""
🚨 ARBITRAGE ALERT

Coin: {coin.upper()}

BUY: {min_ex} {min_price}
SELL: {max_ex} {max_price}

Gross: {percent:.4f}%
Net: {net:.4f}%
"""
                send_msg(msg)

        except Exception as e:
            print(f"{coin} error:", e)

run()
