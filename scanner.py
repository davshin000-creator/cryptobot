import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

coins = {
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
    "SOL-USD": "SOL"
}

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={
        "chat_id": CHAT_ID,
        "text": text
    })

def check_coin(ticker, symbol):
    df = yf.download(
        ticker,
        period="30d",
        interval="1h"
    )

    df = df.dropna()

    if len(df) < 20:
        print(f"{symbol}: not enough data")
        return

    close = df["Close"]

    rsi = RSIIndicator(
        close=close,
        window=14
    )

    df["RSI"] = rsi.rsi()

    latest_price = float(df["Close"].iloc[-1])
    latest_rsi = float(df["RSI"].iloc[-1])

    print(f"{symbol} | Price: {latest_price:.2f} | RSI: {latest_rsi:.2f}")

    if latest_rsi < 30:
        send_msg(f"""
🟢 OVERSOLD ALERT

Coin: {symbol}
Price: ${latest_price:.2f}
RSI: {latest_rsi:.2f}

Possible bounce setup
""")

    elif latest_rsi > 70:
        send_msg(f"""
🔴 OVERBOUGHT ALERT

Coin: {symbol}
Price: ${latest_price:.2f}
RSI: {latest_rsi:.2f}

Possible pullback setup
""")

def run():
    for ticker, symbol in coins.items():
        try:
            check_coin(ticker, symbol)
        except Exception as e:
            print(f"{symbol} error:", e)

run()
