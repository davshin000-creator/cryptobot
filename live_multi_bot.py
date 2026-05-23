import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import yfinance as yf
import csv

from datetime import datetime
from ta.momentum import RSIIndicator

KRAKEN_KEY = os.getenv("KRAKEN_KEY")
KRAKEN_SECRET = os.getenv("KRAKEN_SECRET")
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BUY_RSI = 25
SELL_RSI = 50

COINS = [
    {
        "symbol": "ETH",
        "ticker": "ETH-USD",
        "pair": "ETHUSD",
        "balance_key": "XETH",
        "usd_size": 15,
        "min_balance": 0.0005,
        "precision": 4,
    },
    {
        "symbol": "BTC",
        "ticker": "BTC-USD",
        "pair": "BTCUSD",
        "balance_key": "XXBT",
        "usd_size": 10,
        "min_balance": 0.00001,
        "precision": 6,
    },
    {
        "symbol": "SOL",
        "ticker": "SOL-USD",
        "pair": "SOLUSD",
        "balance_key": "SOL",
        "usd_size": 5,
        "min_balance": 0.01,
        "precision": 3,
    },
]


def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})


def save_trade(symbol, action, price, rsi, ema10, volume, result):
    with open("multi_trade_log.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.utcnow().isoformat(),
            symbol,
            action,
            price,
            rsi,
            ema10,
            volume,
            result
        ])


def kraken_signature(urlpath, data):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(
        base64.b64decode(KRAKEN_SECRET),
        message,
        hashlib.sha512
    )

    return base64.b64encode(mac.digest()).decode()


def kraken_private(endpoint, data=None):
    if data is None:
        data = {}

    urlpath = f"/0/private/{endpoint}"
    url = "https://api.kraken.com" + urlpath

    data["nonce"] = str(int(time.time() * 1000))

    headers = {
        "API-Key": KRAKEN_KEY,
        "API-Sign": kraken_signature(urlpath, data)
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()


def get_balance(balance_key):
    result = kraken_private("Balance")

    if result.get("error"):
        print("Balance error:", result)
        return 0

    balances = result.get("result", {})
    return float(balances.get(balance_key, 0))


def place_order(pair, side, volume):
    data = {
        "ordertype": "market",
        "type": side,
        "volume": volume,
        "pair": pair
    }

    return kraken_private("AddOrder", data)


def get_signal_data(ticker):
    df = yf.download(
        ticker,
        period="30d",
        interval="1h",
        progress=False
    )

    df = df.dropna()

    close = df["Close"].squeeze()

    rsi = RSIIndicator(close=close, window=14)
    df["RSI"] = rsi.rsi()

    df["EMA10"] = close.ewm(span=10).mean()

    price = float(close.iloc[-1])
    rsi_value = float(df["RSI"].iloc[-1])
    ema10 = float(df["EMA10"].iloc[-1])

    return price, rsi_value, ema10


def run_coin(coin):
    symbol = coin["symbol"]

    price, rsi_value, ema10 = get_signal_data(coin["ticker"])
    balance = get_balance(coin["balance_key"])

    print(f"{symbol} Price:", price)
    print(f"{symbol} RSI:", rsi_value)
    print(f"{symbol} EMA10:", ema10)
    print(f"{symbol} Balance:", balance)

    buy_volume = round(
        coin["usd_size"] / price,
        coin["precision"]
    )

    # BUY = oversold + short-term recovery
    buy_signal = (
        rsi_value < BUY_RSI
        and price > ema10
    )

    # SELL = RSI recovery
    sell_signal = (
        rsi_value > SELL_RSI
    )

    if buy_signal:

        if balance >= coin["min_balance"]:
            print(f"{symbol}: Already holding. Skip buy.")

            send_msg(f"""
⚠️ {symbol} BUY SKIPPED

Already holding {symbol}

Balance: {balance}
Price: ${price:.2f}
RSI: {rsi_value:.2f}
EMA10: {ema10:.2f}
""")

        else:
            result = place_order(
                coin["pair"],
                "buy",
                buy_volume
            )

            print(result)

            save_trade(
                symbol,
                "BUY",
                price,
                rsi_value,
                ema10,
                buy_volume,
                result
            )

            send_msg(f"""
🟢 {symbol} AUTO BUY

Price: ${price:.2f}
RSI: {rsi_value:.2f}
EMA10: {ema10:.2f}
Volume: {buy_volume}

Result:
{result}
""")

    elif sell_signal:

        if balance >= coin["min_balance"]:
            sell_volume = round(
                balance,
                coin["precision"]
            )

            result = place_order(
                coin["pair"],
                "sell",
                sell_volume
            )

            print(result)

            save_trade(
                symbol,
                "SELL",
                price,
                rsi_value,
                ema10,
                sell_volume,
                result
            )

            send_msg(f"""
🔴 {symbol} AUTO SELL

Price: ${price:.2f}
RSI: {rsi_value:.2f}
EMA10: {ema10:.2f}
Volume: {sell_volume}

Result:
{result}
""")

        else:
            print(f"{symbol}: No balance to sell.")

    else:
        print(f"{symbol}: No signal.")


for coin in COINS:
    try:
        run_coin(coin)
    except Exception as e:
        print(f"{coin['symbol']} error:", e)
