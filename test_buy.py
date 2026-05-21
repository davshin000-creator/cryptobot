import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

# ==========================
# ENV
# ==========================

KRAKEN_KEY = os.getenv(
    "KRAKEN_KEY"
)

KRAKEN_SECRET = os.getenv(
    "KRAKEN_SECRET"
)

# ==========================
# SETTINGS
# ==========================

PAIR = "ETHUSD"

USD_SIZE = 5

# ==========================
# Kraken Signature
# ==========================

def get_kraken_signature(

    urlpath,
    data,
    secret

):

    postdata = urllib.parse.urlencode(
        data
    )

    encoded = (
        str(data["nonce"])
        + postdata
    ).encode()

    message = (
        urlpath.encode()
        + hashlib.sha256(encoded).digest()
    )

    mac = hmac.new(

        base64.b64decode(secret),
        message,
        hashlib.sha512

    )

    return base64.b64encode(
        mac.digest()
    ).decode()

# ==========================
# Get ETH Price
# ==========================

response = requests.get(

    "https://api.kraken.com"
    "/0/public/Ticker?pair=ETHUSD"

).json()

price = float(

    response["result"]["XETHZUSD"]["c"][0]

)

print(f"ETH Price: {price}")

# ==========================
# Calculate Volume
# ==========================

volume = round(

    USD_SIZE / price,
    4

)

print(f"Volume: {volume}")

# ==========================
# Place Order
# ==========================

urlpath = "/0/private/AddOrder"

url = (
    "https://api.kraken.com"
    + urlpath
)

nonce = str(
    int(time.time() * 1000)
)

data = {

    "nonce": nonce,

    "ordertype": "market",

    "type": "buy",

    "volume": volume,

    "pair": PAIR

}

headers = {

    "API-Key": KRAKEN_KEY,

    "API-Sign": get_kraken_signature(

        urlpath,
        data,
        KRAKEN_SECRET

    )

}

response = requests.post(

    url,
    headers=headers,
    data=data

)

result = response.json()

print(result)
