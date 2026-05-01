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
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        return None

# 💰 Kraken (BTC만)
def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

# 💰 Gemini
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
            # 🔁 거래소 가격 수집
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

            # 🔥 최고가 / 최저가 찾기
            max_ex = max(prices, key=prices.get)
            min_ex = min(prices, key=prices.get)

            max_price = prices[max_ex]
            min_price = prices[min_ex]

            diff = max_price - min_price
            percent = (diff / min_price) * 100

            print(f"{coin} | Gross: {percent:.4f}%")

            # 💰 실전 필터
            fee = 0.4
            net = percent - fee

            min_diff = 50        # 최소 $50 차이
            min_percent = 0.3    # 최소 0.3%

            print(f"{coin} | Net: {net:.4f}% | Diff: ${diff:.2f}")

            # 🚨 진짜 기회만 알림
            if net > min_percent and diff > min_diff:
                msg = f"""
🚨 REAL TRADE OPPORTUNITY

Coin: {coin.upper()}

BUY: {min_ex} {min_price}
SELL: {max_ex} {max_price}

Diff: ${diff:.2f}
Gross: {percent:.4f}%
Net: {net:.4f}%
"""
                send_msg(msg)

        except Exception as e:
            print(f"{coin} error:", e)

# ▶ 실행
run()
