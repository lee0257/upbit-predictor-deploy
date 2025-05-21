import os
import time
import datetime
import traceback
import requests
from supabase import create_client
from pytz import timezone

SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = ["1901931119"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
sent_markets = set()

def get_korean_name(market, all_markets):
    for m in all_markets:
        if m["market"] == market:
            return m["korean_name"]
    return market

def get_markets():
    url = "https://api.upbit.com/v1/market/all"
    response = requests.get(url)
    all_markets = response.json()
    return [m["market"] for m in all_markets if m["market"].startswith("KRW-")], all_markets

def fetch_prices(markets):
    url = f"https://api.upbit.com/v1/ticker?markets={','.join(markets)}"
    response = requests.get(url)
    return response.json()

def send_telegram(msg):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
        except:
            pass

def insert_supabase(record):
    try:
        supabase.table("messages").insert(record).execute()
    except Exception as e:
        print("[Supabase 삽입 오류]", e)

def make_msg(index, market, name, price, reason):
    buy_min = round(price * 0.99, 6)
    buy_max = round(price * 1.005, 6)
    target = round(price * 1.03, 6)

    def format_number(val):
        return f"{val:,.6f}" if val < 1 else f"{val:,.0f}"

    return f"""[추천코인{index}]
- 코인명: {name} ({market})
- 현재가: {format_number(price)}원
- 매수 추천가: {format_number(buy_min)} ~ {format_number(buy_max)}원
- 목표 매도가: {format_number(target)}원
- 예상 수익률: 3%
- 예상 소요 시간: 10분 이내
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""

def should_send(market):
    return market not in sent_markets

def analyze_and_send():
    try:
        markets, all_info = get_markets()
        data = fetch_prices(markets)
        now = datetime.datetime.now(timezone("Asia/Seoul"))
        index = 1

        for item in data:
            market = item["market"]
            price = item["trade_price"]
            acc = item["acc_trade_price_24h"]
            rate = item.get("signed_change_rate", 0)

            if acc < 1200000000 or rate < 0.02:
                continue

            if not should_send(market):
                continue

            name = get_korean_name(market, all_info)
            msg = make_msg(index, market, name, price, "체결량 급증 + 매수 강세 포착")
            send_telegram(msg)
            insert_supabase({
                "timestamp": now.isoformat(),
                "market": market,
                "message": msg
            })
            sent_markets.add(market)
            index += 1

    except Exception as e:
        print("[오류]", e)
        traceback.print_exc()
        send_telegram(f"[에러]\n{str(e)}")

if __name__ == "__main__":
    while True:
        analyze_and_send()
        time.sleep(30)
