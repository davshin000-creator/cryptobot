import requests
import os

# 🔐 GitHub Secrets
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 📊 감시 코인
coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL"
}

# 📩 텔레그램 메시지
def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram error:", e)

# 💰 Coinbase
def coinbase_price(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        return float(requests.get(url).json()["data"]["amount"])
    except:
        return None

# 💰 Kraken (BTC만)
def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        return float(requests.get(url).json()["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

# 💰 Gemini
def gemini_price(symbol):
    try:
        url = f"https://api.gemini.com/v1/pubticker/{symbol.lower()}usd"
        return float(requests.get(url).json()["last"])
    except:
        return None

# 💰 KuCoin
def kucoin_price(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
        return float(requests.get(url).json()["data"]["price"])
    except:
        return None

def run():
    for coin, symbol in coins.items():

        try:
            # 🔁 가격 수집
            prices = {
                "Coinbase": coinbase_price(symbol),
                "Gemini": gemini_price(symbol),
                "KuCoin": kucoin_price(symbol)
            }

            if coin == "bitcoin":
                prices["Kraken"] = kraken_price()

            # None 제거
            prices = {k: v for k, v in prices.items() if v is not None}

            if len(prices) < 2:
                print(f"{coin}: 데이터 부족")
                continue

            # 🔥 최고/최저
            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)

            max_p = prices[max_ex]
            min_p = prices[min_ex]

            diff = max_p - min_p
            percent = (diff / min_p) * 100

            # 💰 수익 계산
            trade_amount = 1000  # 투자금 ($)

            profit = (diff / min_p) * trade_amount

            fee_percent = 0.4
            net_percent = percent - fee_percent

            net_profit = profit * (net_percent / percent) if percent != 0 else 0

            print(f"{coin} | Profit: ${net_profit:.2f}")

            # 🔥 필터 (실전용)
            min_profit = 3  # 최소 $3

            if net_profit > min_profit:
                send_msg(f"""
🚨 REAL PROFIT OPPORTUNITY

Coin: {coin.upper()}

BUY: {min_ex} {min_p}
SELL: {max_ex} {max_p}

Profit: ${net_profit:.2f}
Percent: {net_percent:.3f}%
""")

        except Exception as e:
            print(f"{coin} error:", e)

# ▶ 실행
run()
