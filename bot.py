import requests
import os

# 🔐 GitHub Secrets에서 가져오기
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("텔레그램 전송 실패:", e)

def coinbase_price():
    try:
        url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        data = requests.get(url).json()
        return float(data["data"]["amount"])
    except:
        print("Coinbase 오류")
        return None

def kraken_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        data = requests.get(url).json()
        return float(data["result"]["XXBTZUSD"]["c"][0])
    except:
        print("Kraken 오류")
        return None

def run_once():
    try:
        c1 = coinbase_price()
        c2 = kraken_price()

        if c1 is None or c2 is None:
            print("데이터 없음")
            return

        diff = c1 - c2
        percent = (diff / c2) * 100

        print("Coinbase:", c1)
        print("Kraken:", c2)
        print(f"Diff: {diff} ({percent:.4f}%)")

        # 💰 현실 수익 필터
        if abs(percent) > 0.3:
            msg = f"""
🚨 ARBITRAGE ALERT

Coinbase: {c1}
Kraken: {c2}

Diff: {diff}
Percent: {percent:.4f}%
"""
            send_msg(msg)

    except Exception as e:
        print("전체 에러:", e)

run_once()
