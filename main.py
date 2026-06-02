import os
import json
import pyupbit
import pandas as pd
import requests

ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

TELEGRAM_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TICKER = "KRW-SOL"
COIN = "SOL"

INTERVAL = "minute15"
BUY_KRW = 5000

LOW_LOOKBACK = 12
LOW_TOLERANCE = 0.005

STOP_LOSS = -0.05
BREAK_LOW_STOP = 0.005

TRAILING_START_PROFIT = 0.02
TRAILING_DROP = -0.015

STATE_FILE = "state.json"

upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "highest_price": 0,
            "in_trailing_mode": False
        }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def reset_state():
    save_state({
        "highest_price": 0,
        "in_trailing_mode": False
    })


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 없음")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )
    except Exception as e:
        print("텔레그램 전송 오류:", e)


def get_balance(currency):
    balances = upbit.get_balances()

    for b in balances:
        if b["currency"] == currency:
            return float(b["balance"])

    return 0


def get_avg_buy_price(currency):
    balances = upbit.get_balances()

    for b in balances:
        if b["currency"] == currency:
            return float(b["avg_buy_price"])

    return 0


def add_indicators(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()

    df["macd"] = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"] = df["macd"] - df["signal"]

    df["recent_low"] = df["low"].rolling(LOW_LOOKBACK).min()

    return df


def main():
    print("Upbit SOL 3시간 저점 반등 + 조기 트레일링 봇 시작")

    state = load_state()

    df = pyupbit.get_ohlcv(TICKER, interval=INTERVAL, count=100)

    if df is None or len(df) < 50:
        print("캔들 데이터 부족")
        send_telegram("⚠️ Upbit SOL 봇 오류\n캔들 데이터 부족")
        return

    df = add_indicators(df)

    last = df.iloc[-2]
    prev = df.iloc[-3]

    price = last["close"]

    recent_low = last["recent_low"]
    low_buy_price = recent_low * (1 + LOW_TOLERANCE)
    break_low_price = recent_low * (1 - BREAK_LOW_STOP)

    krw_balance = get_balance("KRW")
    sol_balance = get_balance(COIN)

    position_value = sol_balance * price

    print(f"SOL 현재가: {price}")
    print(f"최근 3시간 최저가: {recent_low}")
    print(f"매수 허용가: {low_buy_price:.2f}")
    print(f"조기손절 기준가: {break_low_price:.2f}")
    print(f"Open: {last['open']}")
    print(f"Close: {last['close']}")
    print(f"MACD Hist: {last['hist']:.4f}")
    print(f"Prev Hist: {prev['hist']:.4f}")
    print(f"KRW 잔고: {krw_balance}")
    print(f"SOL 잔고: {sol_balance}")
    print(f"보유 평가금액: {position_value:.2f}")
    print(f"트레일링 상태: {state}")

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

    if position_value < 5000:
        reset_state()

        if buy_signal:
            if krw_balance >= BUY_KRW:
                print("SOL 매수 실행")

                result = upbit.buy_market_order(TICKER, BUY_KRW)
                print(result)

                reset_state()

                send_telegram(
                    f"🟢 Upbit SOL 매수 실행\n"
                    f"현재가: {price:,.0f}원\n"
                    f"최근 3시간 최저가: {recent_low:,.0f}원\n"
                    f"매수 허용가: {low_buy_price:,.0f}원\n"
                    f"매수금액: {BUY_KRW:,.0f}원\n"
                    f"최종 손절: {STOP_LOSS * 100:.1f}%\n"
                    f"트레일링 시작: +{TRAILING_START_PROFIT * 100:.1f}%\n"
                    f"트레일링 하락폭: {TRAILING_DROP * 100:.1f}%\n"
                    f"양봉 여부: {bullish_candle}\n"
                    f"MACD 회복: {macd_recovering}"
                )

            else:
                print("KRW 잔고 부족")
                send_telegram(
                    f"⚠️ Upbit SOL 매수 실패\n"
                    f"이유: KRW 잔고 부족\n"
                    f"KRW 잔고: {krw_balance:,.0f}원"
                )

        else:
            print("매수 조건 미충족")

    else:
        avg_buy_price = get_avg_buy_price(COIN)

        if avg_buy_price == 0:
            print("평균 매수가 조회 실패")
            send_telegram("⚠️ Upbit SOL 봇 오류\n평균 매수가 조회 실패")
            return

        profit_rate = (price - avg_buy_price) / avg_buy_price

        print(f"평균 매수가: {avg_buy_price}")
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
            sell_reason = "저점 이탈 조기 손절"

        if profit_rate <= STOP_LOSS:
            sell_signal = True
            sell_reason = "최종 손절 -5%"

        if state.get("in_trailing_mode") and trailing_drop_rate <= TRAILING_DROP:
            sell_signal = True
            sell_reason = "조기 트레일링 매도"

        if sell_signal:
            print("SOL 매도 실행")

            result = upbit.sell_market_order(TICKER, sol_balance)
            print(result)

            send_telegram(
                f"🔴 Upbit SOL 매도 실행\n"
                f"이유: {sell_reason}\n"
                f"현재가: {price:,.0f}원\n"
                f"평균 매수가: {avg_buy_price:,.0f}원\n"
                f"최근 3시간 최저가: {recent_low:,.0f}원\n"
                f"최고가: {highest_price:,.0f}원\n"
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
        send_telegram(f"⚠️ Upbit SOL 봇 에러 발생\n{e}")
