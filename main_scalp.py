import os
import time
import json
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
BUY_USD = 18

LOW_LOOKBACK = 24
LOW_TOLERANCE = 0.005

STOP_LOSS = -0.05
BREAK_LOW_STOP = 0.005

TRAILING_START_PROFIT = 0.02
TRAILING_DROP = -0.015

STATE_FILE = "state.json"


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"highest_price": 0, "in_trailing_mode": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def reset_state():
    save_state({"highest_price": 0, "in_trailing_mode": False})


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 없음")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
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
            "time", "open", "high", "low", "close",
            "vwap", "volume", "count"
        ]
    )

    for col in ["open", "high", "low", "close", "vwap", "volume"]:
        df[col] = df[col].astype(float)

    return df


def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

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

    latest_buy = sorted(buys, key=lambda x: x["time"], reverse=True)[0]
    return float(latest_buy["price"])


def main():
    print("Kraken SOL 6시간 저점 + EMA20 회복 자동매매 시작")

    state = load_state()

    df = get_ohlcv()

    if df is None or len(df) < 100:
        print("캔들 부족")
        send_telegram("⚠️ SOL 봇 오류\n캔들 데이터 부족")
        return

    df = add_indicators(df)

    last = df.iloc[-2]
    prev = df.iloc[-3]

    price = last["close"]

    recent_low = last["recent_low"]
    low_buy_price = recent_low * (1 + LOW_TOLERANCE)
    break_low_price = recent_low * (1 - BREAK_LOW_STOP)

    balance = get_balance()

    usd_balance = float(balance.get("ZUSD", 0))
    sol_balance = float(balance.get(ASSET, 0))
    position_value = sol_balance * price

    print(f"SOL 현재가: {price}")
    print(f"최근 6시간 최저가: {recent_low}")
    print(f"매수 허용 가격: {low_buy_price:.4f}")
    print(f"조기손절 기준가: {break_low_price:.4f}")
    print(f"Open: {last['open']}")
    print(f"Close: {last['close']}")
    print(f"EMA20: {last['ema20']:.4f}")
    print(f"Prev EMA20: {prev['ema20']:.4f}")
    print(f"MACD Hist: {last['hist']:.4f}")
    print(f"Prev Hist: {prev['hist']:.4f}")
    print(f"USD 잔고: {usd_balance}")
    print(f"SOL 잔고: {sol_balance}")
    print(f"보유 평가금액: {position_value:.2f}")
    print(f"트레일링 상태: {state}")

    near_recent_low = price <= low_buy_price
    bullish_candle = last["close"] > last["open"]
    macd_recovering = last["hist"] > prev["hist"]
    ema20_recovering = last["close"] > last["ema20"]
    ema20_rising = last["ema20"] > prev["ema20"]

    buy_signal = (
        near_recent_low
        and bullish_candle
        and macd_recovering
        and ema20_recovering
        and ema20_rising
    )

    if position_value < 5:
        reset_state()

        if buy_signal:
            if usd_balance >= BUY_USD:
                print("SOL 6시간 저점 반등 매수 실행")

                result = buy_market()
                print(result)

                reset_state()

                send_telegram(
                    f"🟢 Kraken SOL 매수 실행\n"
                    f"전략: 6시간 저점 + EMA20 회복\n"
                    f"현재가: ${price:.4f}\n"
                    f"최근 6시간 최저가: ${recent_low:.4f}\n"
                    f"매수 허용가: ${low_buy_price:.4f}\n"
                    f"매수금액: ${BUY_USD}\n"
                    f"손절: {STOP_LOSS * 100:.1f}%\n"
                    f"트레일링 시작: +{TRAILING_START_PROFIT * 100:.1f}%\n"
                    f"트레일링 하락폭: {TRAILING_DROP * 100:.1f}%\n"
                    f"양봉: {bullish_candle}\n"
                    f"MACD 회복: {macd_recovering}\n"
                    f"EMA20 회복: {ema20_recovering}\n"
                    f"EMA20 상승: {ema20_rising}"
                )

            else:
                print("USD 잔고 부족")
                send_telegram(
                    f"⚠️ Kraken SOL 매수 실패\n"
                    f"이유: USD 잔고 부족\n"
                    f"USD 잔고: ${usd_balance:.4f}"
                )

        else:
            print("매수 조건 미충족")
            print(f"저점 근처: {near_recent_low}")
            print(f"양봉: {bullish_candle}")
            print(f"MACD 회복: {macd_recovering}")
            print(f"EMA20 회복: {ema20_recovering}")
            print(f"EMA20 상승: {ema20_rising}")

    else:
        avg_buy_price = get_latest_buy_price()

        if avg_buy_price == 0:
            print("매수가 조회 실패")
            send_telegram("⚠️ Kraken SOL 봇 오류\n매수가 조회 실패")
            return

        profit_rate = (price - avg_buy_price) / avg_buy_price

        print(f"매수가: {avg_buy_price}")
        print(f"수익률: {profit_rate * 100:.2f}%")

        if state.get("highest_price", 0) == 0:
            state["highest_price"] = price

        if price > state.get("highest_price", 0):
            state["highest_price"] = price

        if profit_rate >= TRAILING_START_PROFIT:
            state["in_trailing_mode"] = True

        highest_price = state.get("highest_price", price)
        trailing_drop_rate = (price - highest_price) / highest_price

        save_state(state)

        print(f"최고가: {highest_price}")
        print(f"고점 대비 하락률: {trailing_drop_rate * 100:.2f}%")
        print(f"트레일링 모드: {state.get('in_trailing_mode')}")

        sell_signal = False
        sell_reason = ""

        break_low_stop = profit_rate < 0 and price < break_low_price

        if break_low_stop:
            sell_signal = True
            sell_reason = "6시간 저점 이탈 조기손절"

        if profit_rate <= STOP_LOSS:
            sell_signal = True
            sell_reason = "최종 손절 -5%"

        if state.get("in_trailing_mode") and trailing_drop_rate <= TRAILING_DROP:
            sell_signal = True
            sell_reason = "트레일링 익절"

        if sell_signal:
            print("SOL 시장가 매도")

            result = sell_market(sol_balance)
            print(result)

            send_telegram(
                f"🔴 Kraken SOL 매도 실행\n"
                f"이유: {sell_reason}\n"
                f"현재가: ${price:.4f}\n"
                f"매수가: ${avg_buy_price:.4f}\n"
                f"최근 6시간 최저가: ${recent_low:.4f}\n"
                f"조기손절 기준가: ${break_low_price:.4f}\n"
                f"최고가: ${highest_price:.4f}\n"
                f"수익률: {profit_rate * 100:.2f}%\n"
                f"고점 대비 하락률: {trailing_drop_rate * 100:.2f}%\n"
                f"SOL 수량: {sol_balance}"
            )

            reset_state()

        else:
            print("보유 유지")
            save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("에러 발생:", e)
        send_telegram(f"⚠️ Kraken SOL 봇 에러 발생\n{e}")
