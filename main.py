import os
import time
import datetime
import traceback
import requests
from supabase import create_client
from pytz import timezone

# ───── Supabase / Telegram 설정 ─────
SUPABASE_URL = "https://pgixxrmhjzqcqoorinfe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnaXh4cm1oanpxY3Fvb3JpbmZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MDU3MTEsImV4cCI6MjA2MzM4MTcxMX0.EuasFceADEYjrLg_GvczlMnYbBRl3AyqKAOCLMbfaMY"
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = ["1901931119"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

last_sent_time = {}

def get_expected_profit_rate(price, target):
    rate = ((target - price) / price) * 100
    return f"{rate:.1f}%"

def get_expected_time():
    return "10분 이내"

def send_telegram(msg):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": msg}
            )
        except Exception as e:
            print(f"[Telegram 오류]: {e}")

def check_connections():
    try:
        supabase.table("messages").select("*").limit(1).execute()
        print("✅ Supabase에 연결되었습니다.")
        send_telegram("[시스템] ✅ Supabase에 연결되었습니다.")
    except Exception as e:
        print("❌ Supabase 연결 실패:", e)
        send_telegram(f"[시스템 오류] ❌ Supabase 연결 실패: {e}")

    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe")
        if r.status_code == 200:
            print("✅ Telegram에 연결되었습니다.")
            send_telegram("[시스템] ✅ Telegram에 연결되었습니다.")
        else:
            print("❌ Telegram 오류:", r.status_code)
            send_telegram(f"[시스템 오류] ❌ Telegram 응답 오류: {r.status_code}")
    except Exception as e:
        print("❌ Telegram 연결 실패:", e)
        send_telegram(f"[시스템 오류] ❌ Telegram 연결 실패: {e}")

def get_market_info():
    url = "https://api.upbit.com/v1/market/all"
    markets = requests.get(url).json()
    return [m["market"] for m in markets if m["market"].startswith("KRW-")], markets

def get_ticker_data(markets):
    url = f"https://api.upbit.com/v1/ticker?markets={','.join(markets)}"
    return requests.get(url).json()

def get_korean_name(market, market_list):
    for m in market_list:
        if m["market"] == market:
            return m["korean_name"]
    return market

def make_msg(index, market, name, price, reason):
    buy_min = round(price * 0.99, 6)
    buy_max = round(price * 1.005, 6)
    target = round(price * 1.03, 6)

    def fmt(v):
        return f"{v:,.6f}" if v < 1 else f"{v:,.0f}"

    return f"""[추천코인{index}]
- 코인명: {name} ({market})
- 현재가: {fmt(price)}원
- 매수 추천가: {fmt(buy_min)} ~ {fmt(buy_max)}원
- 목표 매도가: {fmt(target)}원
- 예상 수익률: {get_expected_profit_rate(price, target)}
- 예상 소요 시간: {get_expected_time()}
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""

def should_send(market):
    now = datetime.datetime.now()
    if market not in last_sent_time:
        return True
    return (now - last_sent_time[market]).total_seconds() > 1800

def update_sent(market):
    last_sent_time[market] = datetime.datetime.now()

def insert_supabase(record):
    try:
        supabase.table("messages").insert(record).execute()
    except Exception as e:
        print(f"[Supabase 삽입 오류]: {e}")

def analyze():
    try:
        markets, all_info = get_market_info()
        tickers = get_ticker_data(markets)
        now = datetime.datetime.now(timezone("Asia/Seoul"))
        index = 1

        for t in tickers:
            market = t["market"]
            price = t["trade_price"]
            acc_volume = t["acc_trade_price_24h"]
            rate = t.get("signed_change_rate", 0)

            if acc_volume < 1200000000 or rate < 0.02:
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
            update_sent(market)
            index += 1

    except Exception as e:
        print("[오류 발생]", e)
        traceback.print_exc()
        send_telegram(f"[에러 발생]\n{e}")

if __name__ == "__main__":
    check_connections()
    print("▶️ 3분 선행포착 시스템 작동 시작 (30초 주기)")
    while True:
        analyze()
        time.sleep(30)
