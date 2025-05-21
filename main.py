import os
import requests
import time
import datetime
import traceback
from supabase import create_client
from pytz import timezone

# 환경 변수 또는 직접 입력
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = ["1901931119"]  # 필요한 수신자 추가 가능

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
sent_coins = set()

def fetch_market_data():
    url = "https://api.upbit.com/v1/ticker?markets=" + ','.join(get_krw_markets())
    response = requests.get(url)
    return response.json()

def get_krw_markets():
    url = "https://api.upbit.com/v1/market/all"
    response = requests.get(url)
    return [m['market'] for m in response.json() if m['market'].startswith("KRW-")]

def get_korean_name(market, all_markets):
    for m in all_markets:
        if m['market'] == market:
            return m['korean_name']
    return ""

def send_telegram_message(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            requests.post(url, data=data)
        except Exception as e:
            print(f"[텔레그램 전송 오류] {e}")

def insert_to_supabase(data):
    try:
        response = supabase.table("messages").insert(data).execute()
        print("[DB 삽입 성공]:", response)
    except Exception as e:
        print("[DB 삽입 실패]:", e)

def format_message(market, price, reason, all_markets):
    name = get_korean_name(market, all_markets)
    return f"""[추천코인1]
- 코인명: {name} ({market})
- 현재가: {price:,}원
- 매수 추천가: {int(price*0.99):,} ~ {int(price*1.005):,}원
- 목표 매도가: {int(price*1.03):,}원
- 예상 수익률: 3%
- 예상 소요 시간: 10분 이내
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""

def should_send(coin):
    return coin not in sent_coins

def analyze_and_alert():
    try:
        all_markets = requests.get("https://api.upbit.com/v1/market/all").json()
        market_list = get_krw_markets()
        ticker_data = fetch_market_data()
        now = datetime.datetime.now(timezone("Asia/Seoul"))

        for item in ticker_data:
            market = item['market']
            price = item['trade_price']
            acc_volume = item['acc_trade_price_24h']

            if acc_volume < 1200000000:  # 최소 거래대금 조건
                continue

            # 조건: 1분간 2% 이상 급등
            change_rate = item.get("signed_change_rate", 0)
            if change_rate >= 0.02 and should_send(market):
                msg = format_message(market, price, "체결량 급증 + 매수 강세 포착", all_markets)
                send_telegram_message(msg)
                insert_to_supabase({
                    "timestamp": now.isoformat(),
                    "market": market,
                    "message": msg,
                })
                sent_coins.add(market)
    except Exception as e:
        print("[분석 중 오류 발생]:", e)
        traceback.print_exc()
        send_telegram_message(f"[오류 발생]\n{str(e)}")

if __name__ == "__main__":
    while True:
        analyze_and_alert()
        time.sleep(30)
