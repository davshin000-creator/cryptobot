import os
import requests
import pyupbit

ip = requests.get("https://api.ipify.org").text
print("현재 GitHub Actions IP:", ip)

access = os.environ.get("UPBIT_ACCESS_KEY")
secret = os.environ.get("UPBIT_SECRET_KEY")

if not access or not secret:
    raise Exception("API 키 없음")

upbit = pyupbit.Upbit(access, secret)

print("업비트 연결 테스트 시작")

balances = upbit.get_balances()
print("잔고 조회 결과:")
print(balances)

price = pyupbit.get_current_price("KRW-BTC")
print("BTC 현재가:")
print(price)

print("테스트 완료")
