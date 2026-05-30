import os
import time
import base64
import hashlib
import hmac
import urllib.parse
import requests
import pandas as pd

API_KEY = os.getenv("KRAKEN_API_KEY")
API_SECRET = os.getenv("KRAKEN_API_SECRET")

TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api.kraken.com"

PAIR = "SOLUSD"
ASSET = "SOL"

INTERVAL = 15
BUY_USD = 15

LOW_LOOKBACK = 4
LOW_TOLERANCE = 0.015

TAKE_PROFIT = 0.015
STOP_LOSS = -0.02


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 없음")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )

        if response.status_code != 200:
            print("텔레그램 전송 실패:", response.text)

    except Exception as e:
        print("텔레그램 전송 오류:", e)


def kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def kraken_private(endpoint, data=None):
    if data is None:
        data = {}

    urlpath = f"/0/private/{endpoint}"
    data["nonce"] = str(int(time.time() * 1000))

    headers = {
        "API-Key": API_KEY,
        "API-Sign": kraken_signature(urlpath, data, API_SECRET),
    }

    response = requests.post(BASE_URL + urlpath, headers=headers, data=data, timeout=20)
    result = response.json()

    if result.get("error"):
        raise Exception(result["error"])

    return result["result"]


def kraken_public(endpoint, params=None):
    response = requests.get(
        BASE_URL + f"/0/public/{endpoint}",
        params=params,
        timeout=20
    )

    result = response.json()

    if result.get("error"):
        raise Exception(result["error"])

    return result["result"]


def get_ohlcv():
    data = kraken_public("OHLC", {"pair": PAIR, "interval": INTERVAL})
    key = [k for k in data.keys() if k != "last"][0]
    rows = data[key]

    df = pd.DataFrame(
        rows,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "volume",
            "count"
        ]
    )

    for col in ["open", "high", "low", "close", "vwap", "volume"]:
        df[col] = df[col].astype(float)

    return df


def add_indicators(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()

    df["macd"] = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"] = df["macd"] - df["signal"]

    df["recent_low"] = df["low"].rolling(LOW_LOOKBACK).min()

    return df


def get_balance():
    return kraken_private("Balance")


def buy_market():
    data = {
        "pair": PAIR,
        "type": "buy",
        "ordertype": "market",
        "volume": str(BUY_USD),
        "oflags": "viqc"
    }

    return kraken_private("AddOrder", data)


def sell_market(sol_amount):
    data = {
        "pair": PAIR,
        "type": "sell",
        "ordertype": "market",
        "volume": str(sol_amount)
    }

    return kraken_private("AddOrder", data)


def get_latest_buy_price():
    trades = kraken_private("TradesHistory", {"type": "all"})
    trade_list = trades.get("trades", {})

    buys = []

    for trade_id, trade in trade_list.items():
        if trade.get("type") == "buy" and "SOL" in trade.get("pair", ""):
            buys.append(trade)

    if not buys:
        return 0

    latest_buy = sorted(
        buys,
        key=lambda x: x["time"],
        reverse=True
    )[0]

    return float(latest_buy["price"])


def main():
    print("Kraken SOL 단타 자동매매 시작")

    df = get_ohlcv()

    if df is None or len(df) < 100:
        print("캔들 부족")
        send_telegram("⚠️ SOL 단타 봇 오류\n캔들 데이터 부족")
        return

    df = add_indicators(df)

    last = df.iloc[-2]
    prev = df.iloc[-3]

    price = last["close"]

    recent_low = last["recent_low"]
    low_buy_price = recent_low * (1 + LOW_TOLERANCE)

    balance = get_balance()

    usd_balance = float(balance.get("ZUSD", 0))
    sol_balance = float(balance.get(ASSET, 0))

    print(f"SOL 현재가: {price}")
    print(f"최근 1시간 최저가: {recent_low}")
    print(f"매수 허용 가격: {low_buy_price:.4f}")
    print(f"Open: {last['open']}")
    print(f"Close: {last['close']}")
    print(f"MACD Hist: {last['hist']:.4f}")
    print(f"Prev Hist: {prev['hist']:.4f}")
    print(f"USD 잔고: {usd_balance}")
    print(f"SOL 잔고: {sol_balance}")

    near_recent_low = price <= low_buy_price
    bullish_candle = last["close"] > last["open"]
    macd_recovering = last["hist"] > prev["hist"]

    buy_signal = (
        near_recent_low
        and (
            bullish_candle
            or macd_recovering
        )
    )

    position_value = sol_balance * price

    if position_value < 5:
        if buy_signal:
            if usd_balance >= BUY_USD:
                print("SOL 단타 매수 실행")

                result = buy_market()
                print(result)

                send_telegram(
                    f"🟢 SOL 단타 매수 실행\n"
                    f"현재가: ${price:.4f}\n"
                    f"최근 1시간 최저가: ${recent_low:.4f}\n"
                    f"매수 허용가: ${low_buy_price:.4f}\n"
                    f"매수금액: ${BUY_USD}\n"
                    f"익절: +{TAKE_PROFIT * 100:.1f}%\n"
                    f"손절: {STOP_LOSS * 100:.1f}%\n"
                    f"양봉 여부: {bullish_candle}\n"
                    f"MACD 회복: {macd_recovering}"
                )

            else:
                print("USD 잔고 부족")
                send_telegram(
                    f"⚠️ SOL 단타 매수 실패\n"
                    f"이유: USD 잔고 부족\n"
                    f"USD 잔고: ${usd_balance:.4f}"
                )

        else:
            print("매수 조건 미충족")

    else:
        avg_buy_price = get_latest_buy_price()

        if avg_buy_price == 0:
            print("매수가 조회 실패")
            send_telegram("⚠️ SOL 단타 봇 오류\n매수가 조회 실패")
            return

        profit_rate = (price - avg_buy_price) / avg_buy_price

        print(f"매수가: {avg_buy_price}")
        print(f"수익률: {profit_rate * 100:.2f}%")

        sell_signal = False
        sell_reason = ""

        if profit_rate >= TAKE_PROFIT:
            print("2% 익절 조건")
            sell_signal = True
            sell_reason = "2% 익절"

        if profit_rate <= STOP_LOSS:
            print("2% 손절 조건")
            sell_signal = True
            sell_reason = "2% 손절"

        if sell_signal:
            print("SOL 단타 시장가 매도")

            result = sell_market(sol_balance)
            print(result)

            send_telegram(
                f"🔴 SOL 단타 매도 실행\n"
                f"이유: {sell_reason}\n"
                f"현재가: ${price:.4f}\n"
                f"매수가: ${avg_buy_price:.4f}\n"
                f"수익률: {profit_rate * 100:.2f}%\n"
                f"SOL 수량: {sol_balance}"
            )

        else:
            print("보유 유지")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("에러 발생:", e)
        send_telegram(f"⚠️ SOL 단타 봇 에러 발생\n{e}")
