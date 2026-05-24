import os
import pyupbit

access = os.environ.get("UPBIT_ACCESS_KEY")
secret = os.environ.get("UPBIT_SECRET_KEY")

if not access or not secret:
    raise Exception("API 키가 없습니다. GitHub Secrets를 확인하세요.")

upbit = pyupbit.Upbit(access, secret)

print("업비트 연결 테스트 시작")

balances = upbit.get_balances()
print("잔고 조회 결과:")
print(balances)

price = pyupbit.get_current_price("KRW-BTC")
print("BTC 현재가:")
print(price)

print("테스트 완료")
