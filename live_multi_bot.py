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

BASE_URL = "https://api.kraken.com"

PAIRS = [
    {"pair": "XBTUSD", "asset": "XXBT", "name": "BTC"},
    {"pair": "ETHUSD", "asset": "XETH", "name": "ETH"},
    {"pair": "SOLUSD", "asset": "SOL", "name": "SOL"},
]

INTERVAL = 15
BUY_USD = 5

RSI_BUY = 40
RSI_SELL = 60

STOP_LOSS = -0.02
TAKE_PROFIT = 0.035


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
    response = requests.get(BASE_URL + f"/0/public/{endpoint}", params=params, timeout=20)
    result = response.json()

    if result.get("error"):
        raise Exception(result["error"])

    return result["result"]


def get_ohlcv(pair):
    data = kraken_public("OHLC", {"pair": pair, "interval": INTERVAL})
    key = [k for k in data.keys() if k != "last"][0]
    rows = data[key]

    df = pd.DataFrame(
        rows,
        columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    )

    for col in ["open", "high", "low", "close", "vwap", "volume"]:
        df[col] = df[col].astype(float)

    return df


def get_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    df["rsi"] = get_rsi(df)

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()

    df["macd"] = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"] = df["macd"] - df["signal"]

    df["vol_ma20"] = df["volume"].rolling(20).mean()

    return df


def get_balance():
    return kraken_private("Balance")


def buy_market(pair):
    data = {
        "pair": pair,
        "type": "buy",
        "ordertype": "market",
        "volume": str(BUY_USD),
        "oflags": "viqc"
    }
    return kraken_private("AddOrder", data)


def sell_market(pair, coin_amount):
    data = {
        "pair": pair,
        "type": "sell",
        "ordertype": "market",
        "volume": str(coin_amount)
    }
    return kraken_private("AddOrder", data)


def get_latest_buy_price(pair):
    trades = kraken_private("TradesHistory", {"type": "all"})
    trade_list = trades.get("trades", {})

    buys = []

    for trade_id, trade in trade_list.items():
        if trade.get("type") == "buy" and pair.replace("USD", "ZUSD") in trade.get("pair", ""):
            buys.append(trade)

    if not buys:
        return 0

    latest_buy = sorted(buys, key=lambda x: x["time"], reverse=True)[0]
    return float(latest_buy["price"])


def run_bot(pair_info):
    pair = pair_info["pair"]
    asset = pair_info["asset"]
    name = pair_info["name"]

    print(f"\n===== {name} 체크 시작 =====")

    df = get_ohlcv(pair)

    if df is None or len(df) < 100:
        print(f"{name} 캔들 데이터 부족")
        return

    df = add_indicators(df)

    last = df.iloc[-2]
    prev = df.iloc[-3]

    price = last["close"]

    balance = get_balance()
    usd_balance = float(balance.get("ZUSD", 0))
    coin_balance = float(balance.get(asset, 0))

    print(f"{name} 현재가: {price}")
    print(f"RSI: {last['rsi']:.2f}")
    print(f"EMA20: {last['ema20']:.2f}")
    print(f"EMA50: {last['ema50']:.2f}")
    print(f"MACD Hist: {last['hist']:.4f}")
    print(f"Prev Hist: {prev['hist']:.4f}")
    print(f"Volume: {last['volume']:.2f}")
    print(f"Vol MA20: {last['vol_ma20']:.2f}")
    print(f"USD 잔고: {usd_balance}")
    print(f"{name} 잔고: {coin_balance}")

    uptrend = last["ema20"] > last["ema50"]
    rsi_pullback = last["rsi"] < RSI_BUY
    macd_reversal = last["hist"] > prev["hist"]
    volume_confirm = last["volume"] > last["vol_ma20"] * 1.2

    buy_signal = uptrend and rsi_pullback and macd_reversal and volume_confirm

    position_value = coin_balance * price

    if position_value < 3:
        if buy_signal:
            if usd_balance >= BUY_USD:
                print(f"{name} 매수 조건 충족 - ${BUY_USD} 매수")
                result = buy_market(pair)
                print(result)
            else:
                print("USD 잔고 부족")
        else:
            print(f"{name} 매수 조건 미충족")

    else:
        avg_buy_price = get_latest_buy_price(pair)

        if avg_buy_price == 0:
            print(f"{name} 최근 매수가 확인 실패")
            return

        profit_rate = (price - avg_buy_price) / avg_buy_price

        print(f"{name} 최근 매수가: {avg_buy_price}")
        print(f"{name} 수익률: {profit_rate * 100:.2f}%")

        sell_signal = False

        if last["rsi"] >= RSI_SELL:
            print(f"{name} RSI 익절 조건")
            sell_signal = True

        if profit_rate <= STOP_LOSS:
            print(f"{name} 손절 조건")
            sell_signal = True

        if profit_rate >= TAKE_PROFIT:
            print(f"{name} 익절 조건")
            sell_signal = True

        if last["ema20"] < last["ema50"]:
            print(f"{name} 추세 이탈 조건")
            sell_signal = True

        if sell_signal:
            print(f"{name} 시장가 매도")
            result = sell_market(pair, coin_balance)
            print(result)
        else:
            print(f"{name} 보유 유지")


def main():
    print("Kraken BTC / ETH / SOL 자동매매 시작")

    for pair_info in PAIRS:
        try:
            run_bot(pair_info)
            time.sleep(2)
        except Exception as e:
            print(f"{pair_info['name']} 에러 발생:", e)


if __name__ == "__main__":
    main()
