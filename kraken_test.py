import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

KRAKEN_KEY = os.getenv("KRAKEN_KEY")
KRAKEN_SECRET = os.getenv("KRAKEN_SECRET")

print("KRAKEN_KEY exists:", KRAKEN_KEY is not None)
print("KRAKEN_SECRET exists:", KRAKEN_SECRET is not None)

def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)

    encoded = (
        str(data["nonce"]) + postdata
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

def kraken_private_request(endpoint, data):

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

    return response.json()

# ==========================
# TEST BALANCE
# ==========================

result = kraken_private_request(
    "Balance",
    {}
)

print(result)
