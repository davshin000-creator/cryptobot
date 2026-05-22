import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import yfinance as yf
from ta.momentum import RSIIndicator

KRAKEN_KEY = os.getenv("KRAKEN_KEY")
KRAKEN_SECRET = os.getenv("KRAKEN_SECRET")
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PAIR = "ETHUSD"
USD_SIZE = 5

BUY_RSI = 25
SELL_RSI = 80
MIN_ETH_BALANCE = 0.0005

def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

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

def get_eth_balance():
    result = kraken_private("Balance")

    if result.get("error"):
        print("Balance error:", result)
        return 0

    balances = result.get("result", {})

    eth_balance = float(
        balances.get("XETH", 0)
    )

    return eth_balance

def place_order(side, volume):
    data = {
        "ordertype": "market",
        "type": side,
        "volume": volume,
        "pair": PAIR
    }

    return kraken_private("AddOrder", data)

def get_eth_rsi():
    df = yf.download(
        "ETH-USD",
        period="30d",
        interval="1h",
        progress=False
    )

    df = df.dropna()
    close = df["Close"]

    rsi = RSIIndicator(
        close=close,
        window=14
    )

    df["RSI"] = rsi.rsi()

    price = float(df["Close"].iloc[-1])
    rsi_value = float(df["RSI"].iloc[-1])

    return price, rsi_value

price, rsi_value = get_eth_rsi()
eth_balance = get_eth_balance()

print("ETH Price:", price)
print("RSI:", rsi_value)
print("ETH Balance:", eth_balance)

buy_volume = round(USD_SIZE / price, 4)

if rsi_value < BUY_RSI:

    if eth_balance >= MIN_ETH_BALANCE:
        print("Already holding ETH. Skip buy.")
        send_msg(f"""
⚠️ BUY SKIPPED

Already holding ETH.

ETH Balance: {eth_balance}
RSI: {rsi_value:.2f}
""")
    else:
        result = place_order("buy", buy_volume)

        send_msg(f"""
🟢 AUTO BUY

ETH Price: ${price:.2f}
RSI: {rsi_value:.2f}
Volume: {buy_volume}

Result:
{result}
""")

elif rsi_value > SELL_RSI:

    if eth_balance >= MIN_ETH_BALANCE:
        sell_volume = round(eth_balance, 4)
        result = place_order("sell", sell_volume)

        send_msg(f"""
🔴 AUTO SELL

ETH Price: ${price:.2f}
RSI: {rsi_value:.2f}
Volume: {sell_volume}

Result:
{result}
""")
    else:
        print("No ETH to sell.")

else:
    print("No signal.")
