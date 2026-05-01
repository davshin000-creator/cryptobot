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

# 💰 Coinbase 가격
def coinbase_price(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        return None

# 💰 Kraken (BTC 전용)
def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

# 💰 CoinGecko (알트코인)
def coingecko_price(coin):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin, "vs_currencies": "usd"}
        data = requests.get(url, params=params).json()
        return float(data[coin]["usd"])
    except:
        return None

# 🚀 실행 로직
def run():
    for coin, symbol in coins.items():
        try:

            # BTC는 Kraken 비교, 나머지는 CoinGecko
            if coin == "bitcoin":
                c1 = coinbase_price(symbol)
                c2 = kraken_price()
            else:
                c1 = coinbase_price(symbol)
                c2 = coingecko_price(coin)

            if c1 is None or c2 is None:
                print(f"{coin}: 데이터 없음")
                continue

            diff = c1 - c2
            percent = (diff / c2) * 100

            print(f"{coin} | Gross: {percent:.4f}%")

            # 💰 현실 수익 계산 (수수료 포함)
            fee = 0.4  # 거래 + 슬리피지 추정
            net_percent = abs(percent) - fee

            print(f"{coin} | Net: {net_percent:.4f}%")

            # 🔥 진짜 기회 필터
            if net_percent > 0.2:
                msg = f"""
🚨 REAL ARBITRAGE

Coin: {coin}

Gross: {percent:.4f}%
Net: {net_percent:.4f}%

Coinbase: {c1}
Other: {c2}
"""
                send_msg(msg)

        except Exception as e:
            print(f"{coin} error:", e)

# ▶ 실행
run()
