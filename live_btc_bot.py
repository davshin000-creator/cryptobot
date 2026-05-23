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

PAIR = "BTCUSD"

USD_SIZE = 10

BUY_RSI = 27
SELL_RSI = 40

MIN_BTC_BALANCE = 0.00001


def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.get(
        url,
        params={
            "chat_id": CHAT_ID,
            "text": msg
        }
    )


def save_trade(action, price, rsi, volume, result):
    with open("btc_trade_log.csv", "a", newline="") as file:
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

    encoded = (
        str(data["nonce"]) + postdata
    ).encode()

    message = (
        urlpath.encode()
        + hashlib.sha256(encoded).digest()
    )

    mac = hmac.new(
        base64.b64decode(KRAKEN_SECRET),
        message,
        hashlib.sha512
    )

    return base64.b64encode(
        mac.digest()
    ).decode()


def kraken_private(endpoint, data=None):

    if data is None:
        data = {}

    urlpath = f"/0/private/{endpoint}"

    url = (
        "https://api.kraken.com"
        + urlpath
    )

    data["nonce"] = str(
        int(time.time() * 1000)
    )

    headers = {

        "API-Key": KRAKEN_KEY,

        "API-Sign": kraken_signature(
            urlpath,
            data
        )
    }

    response = requests.post(
        url,
        headers=headers,
        data=data
    )

    return response.json()


def get_btc_balance():

    result = kraken_private(
        "Balance"
    )

    if result.get("error"):

        print(
            "Balance error:",
            result
        )

        return 0

    balances = result.get(
        "result",
        {}
    )

    btc_balance = float(
        balances.get("XXBT", 0)
    )

    return btc_balance


def place_order(side, volume):

    data = {

        "ordertype": "market",

        "type": side,

        "volume": volume,

        "pair": PAIR

    }

    return kraken_private(
        "AddOrder",
        data
    )


def get_btc_rsi():

    df = yf.download(

        "BTC-USD",

        period="30d",

        interval="1h",

        progress=False

    )

    df = df.dropna()

    close = df["Close"].squeeze()

    rsi = RSIIndicator(

        close=close,

        window=14

    )

    df["RSI"] = rsi.rsi()

    latest_price = float(
        close.iloc[-1]
    )

    latest_rsi = float(
        df["RSI"].iloc[-1]
    )

    return latest_price, latest_rsi


# ==========================
# MAIN
# ==========================

price, rsi_value = get_btc_rsi()

btc_balance = get_btc_balance()

print("BTC Price:", price)
print("RSI:", rsi_value)
print("BTC Balance:", btc_balance)

buy_volume = round(
    USD_SIZE / price,
    6
)

# ==========================
# BUY
# ==========================

if rsi_value < BUY_RSI:

    if btc_balance >= MIN_BTC_BALANCE:

        print("Already holding BTC.")

        send_msg(f"""

⚠️ BTC BUY SKIPPED

Already holding BTC.

BTC Balance:
{btc_balance}

RSI:
{rsi_value:.2f}

BTC Price:
${price:.2f}

""")

    else:

        result = place_order(
            "buy",
            buy_volume
        )

        print(result)

        save_trade(
            "BUY",
            price,
            rsi_value,
            buy_volume,
            result
        )

        send_msg(f"""

🟢 BTC AUTO BUY

BTC Price:
${price:.2f}

RSI:
{rsi_value:.2f}

Volume:
{buy_volume}

Result:
{result}

""")

# ==========================
# SELL
# ==========================

elif rsi_value > SELL_RSI:

    if btc_balance >= MIN_BTC_BALANCE:

        sell_volume = round(
            btc_balance,
            6
        )

        result = place_order(
            "sell",
            sell_volume
        )

        print(result)

        save_trade(
            "SELL",
            price,
            rsi_value,
            sell_volume,
            result
        )

        send_msg(f"""

🔴 BTC AUTO SELL

BTC Price:
${price:.2f}

RSI:
{rsi_value:.2f}

Volume:
{sell_volume}

Result:
{result}

""")

    else:

        print("No BTC to sell.")

# ==========================
# NO SIGNAL
# ==========================

else:

    print("No signal.")
