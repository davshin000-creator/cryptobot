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

# Coinbase 가격 (공통)
def coinbase_price(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        return None

# Kraken (BTC만 예시 유지)
def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        return None

# CoinGecko (알트코인용)
def coingecko_price(coin):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin, "vs_currencies": "usd"}
        data = requests.get(url, params=params).json()
        return float(data[coin]["usd"])
    except:
        return None

def run():
    for coin, symbol in coins.items():
        try:
            # BTC는 Kraken 비교, 나머지는 CoinGecko 비교
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

            print(f"{coin} -> {percent:.4f}%")

            # 💰 현실 필터 (0.5% 이상만)
            if abs(percent) > 0.5:
                msg = f"""
🚨 ARBITRAGE DETECTED

Coin: {coin}
Price A: {c1}
Price B: {c2}

Diff: {diff}
fee = 0.4  # 총 수수료 + 리스크 (0.4%)

net_percent = abs(percent) - fee

print(f"Gross: {percent:.4f}% | Net: {net_percent:.4f}%")

if net_percent > 0.2:
    send_msg(f"""
🚨 REAL ARBITRAGE

Coin: {coin}
Gross: {percent:.4f}%
Net: {net_percent:.4f}%

Opportunity confirmed
""")
