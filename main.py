import os
import time
import datetime
import traceback
import requests
from supabase import create_client
from pytz import timezone

# ────────────────────────────────────────────────────────
# 🔧 설정: Supabase / Telegram
# ────────────────────────────────────────────────────────
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8..."
TELEGRAM_CHAT_IDS = ["1901931119"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────
# ✅ 중복 방지: 최근 전송 시간 기록
# ────────────────────────────────────────────────────────
last_sent_time = {}

# ────────────────────────────────────────────────────────
# ✅ 연결 확인 함수 (시작 시 단 1회)
# ────────────────────────────────────────────────────────
def check_supabase():
    try:
        supabase.table("messages").select("*").limit(1).execute()
        print("✅ Supabase 연결되었습니다.")
    except Exception as e:
        print("❌ Supabase 연결 실패:", e)

def check_telegram():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        res = requests.get(url)
        if res.status_code == 200:
            print("✅ Telegram 연결되었습니다.")
        else:
            print("❌ Telegram 응답 오류:", res.status_code)
    except Exception as e:
        print("❌ Telegram 연결 실패:", e)

# ────────────────────────────────────────────────────────
# 📈 유틸: 수익률 및 시간 계산
# ────────────────────────────────────────────────────────
def get_expected_profit_rate(price, target):
    rate = ((target - price) / price) * 100
    return f"{rate:.1f}%"

def get_expected_time():
    return "10분 이내"

# ────────────────────────────────────────────────────────
# 📋 데이터 관련 함수
# ────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────
# 📬 메시지 전송 및 저장
# ────────────────────────────────────────────────────────
def send_telegram(msg):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
        except Exception as e:
            print(f"[텔레그램 전송 오류]: {e}")

def insert_supabase(record):
    try:
        supabase.table("messages").insert(record).execute()
    except Exception as e:
        print("[Supabase 삽입 오류]", e)

# ────────────────────────────────────────────────────────
# 📦 메시지 생성
# ────────────────────────────────────────────────────────
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
- 예상 수익률: {get_expected_profit_rate(price, target)}
- 예상 소요 시간: {get_expected_time()}
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""

# ────────────────────────────────────────────────────────
# ✅ 중복 전송 체크
# ────────────────────────────────────────────────────────
def should_send(market):
    now = datetime.datetime.now()
    if market not in last_sent_time:
        return True
    return (now - last_sent_time[market]).total_seconds() > 1800

def update_sent(market):
    last_sent_time[market] = datetime.datetime.now()

# ────────────────────────────────────────────────────────
# 🚀 메인 분석 루프
# ────────────────────────────────────────────────────────
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
            update_sent(market)
            index += 1

    except Exception as e:
        print("[분석 오류]", e)
        traceback.print_exc()
        send_telegram(f"[에러 발생]\n{str(e)}")

# ────────────────────────────────────────────────────────
# ▶️ 실행 시작
# ────────────────────────────────────────────────────────
if __name__ == "__main__":
    check_supabase()
    check_telegram()
    print("✅ 서버 정상 작동 시작됨 (30초 주기)\n──────────────────────────────")
    while True:
        analyze_and_send()
        time.sleep(30)
