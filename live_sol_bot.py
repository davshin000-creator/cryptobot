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

PAIR = "SOLUSD"

USD_SIZE = 5

BUY_RSI = 27
SELL_RSI = 40

MIN_SOL_BALANCE = 0.01


def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})


def save_trade(action, price, rsi, volume, result):
    with open("sol_trade_log.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.utcnow().isoformat(),
            action,
            price,
            rsi,
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


def get_sol_balance():
    result = kraken_private("Balance")

    if result.get("error"):
        print("Balance error:", result)
        return 0

    balances = result.get("result", {})

    return float(balances.get("SOL", 0))


def place_order(side, volume):
    data = {
        "ordertype": "market",
        "type": side,
        "volume": volume,
        "pair": PAIR
    }

    return kraken_private("AddOrder", data)


def get_sol_rsi():
    df = yf.download(
        "SOL-USD",
        period="30d",
        interval="1h",
        progress=False
    )

    df = df.dropna()
    close = df["Close"].squeeze()

    rsi = RSIIndicator(close=close, window=14)
    df["RSI"] = rsi.rsi()

    latest_price = float(close.iloc[-1])
    latest_rsi = float(df["RSI"].iloc[-1])

    return latest_price, latest_rsi


price, rsi_value = get_sol_rsi()
sol_balance = get_sol_balance()

print("SOL Price:", price)
print("RSI:", rsi_value)
print("SOL Balance:", sol_balance)

buy_volume = round(USD_SIZE / price, 3)


if rsi_value < BUY_RSI:

    if sol_balance >= MIN_SOL_BALANCE:
        print("Already holding SOL.")

        send_msg(f"""
⚠️ SOL BUY SKIPPED

Already holding SOL.

SOL Balance: {sol_balance}
RSI: {rsi_value:.2f}
SOL Price: ${price:.2f}
""")

    else:
        result = place_order("buy", buy_volume)

        print(result)

        save_trade("BUY", price, rsi_value, buy_volume, result)

        send_msg(f"""
🟢 SOL AUTO BUY

SOL Price: ${price:.2f}
RSI: {rsi_value:.2f}
Volume: {buy_volume}

Result:
{result}
""")


elif rsi_value > SELL_RSI:

    if sol_balance >= MIN_SOL_BALANCE:
        sell_volume = round(sol_balance, 3)

        result = place_order("sell", sell_volume)

        print(result)

        save_trade("SELL", price, rsi_value, sell_volume, result)

        send_msg(f"""
🔴 SOL AUTO SELL

SOL Price: ${price:.2f}
RSI: {rsi_value:.2f}
Volume: {sell_volume}

Result:
{result}
""")

    else:
        print("No SOL to sell.")


else:
    print("No signal.")
