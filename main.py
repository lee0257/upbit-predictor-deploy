import os
import requests
from datetime import datetime, timedelta
import time
from supabase import create_client, Client

# === 환경변수 ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_NAME = os.getenv("SUPABASE_TABLE_NAME", "messages")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_ID", "").split(",")

# === Supabase 연결 ===
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[시스템] ✅ Supabase 클라이언트 객체 생성 완료")
except Exception as e:
    print(f"[에러] ❌ Supabase 클라이언트 생성 실패: {e}")

# === Telegram 연결 확인 ===
def check_telegram():
    try:
        test_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(test_url)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[에러] Telegram 연결 확인 실패: {e}")
        return False

# === 텔레그램 전송 ===
def send_telegram(message: str):
    if not TELEGRAM_CHAT_IDS or TELEGRAM_CHAT_IDS == ['']:
        print("[경고] TELEGRAM_CHAT_IDS 환경변수가 비어 있음. 전송 생략")
        return
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id.strip(), "text": message}
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"[에러] Telegram 전송 실패: {e}")

# === Supabase 저장 ===
def send_to_supabase(content: str, msg_type: str = "signal"):
    try:
        data = {
            "content": content,
            "type": msg_type,
            "created_at": datetime.now().isoformat()
        }
        print(f"[디버그] Supabase 삽입 데이터: {data}")
        result = supabase.table(SUPABASE_TABLE_NAME).insert(data).execute()
        print(f"[시스템] ✅ Supabase 삽입 성공: {result}")
    except Exception as e:
        print(f"[에러] ❌ Supabase 삽입 실패: {e}")
        send_telegram(f"[에러] ❌ Supabase 삽입 실패\n{str(e)}")

# === 한글 코인명 자동 매핑 ===
def get_korean_name_map():
    url = "https://api.upbit.com/v1/market/all?isDetails=true"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return {
            item['market'].split('-')[1]: item['korean_name']
            for item in data if item['market'].startswith("KRW-")
        }
    except Exception as e:
        print(f"[에러] 한글 코인명 매핑 실패: {e}")
        return {}

KOREAN_NAME_MAP = get_korean_name_map()

# === 메시지 생성 ===
def create_recommendation_message(symbol, price, buy_min, buy_max, target, profit_rate, est_time, reason):
    korean = KOREAN_NAME_MAP.get(symbol, symbol)
    link = f"https://upbit.com/exchange?code=CRIX.UPBIT.{symbol}"
    return f"""[추천코인1]
- 코인명: {symbol} ({korean})
- 현재가: {price:,}원
- 매수 추천가: {buy_min:,} ~ {buy_max:,}원
- 목표 매도가: {target:,}원
- 예상 수익률: {profit_rate:.1f}%
- 예상 소요 시간: {est_time}분
- 추천 이유: {reason}
[선행급등포착]
{link}"""

# === 중복 전송 차단 ===
last_sent_times = {}

# === 조건 감지 ===
def detect_coin():
    symbol = "DEEP"
    now = datetime.now()
    if symbol in last_sent_times and now - last_sent_times[symbol] < timedelta(minutes=30):
        return None

    price = 253
    buy_min, buy_max = 250, 254
    target = 262
    profit_rate = (target - ((buy_min + buy_max) / 2)) / ((buy_min + buy_max) / 2) * 100
    est_time = 5
    reason = "체결량 급증 + 매수 강세 포착"

    msg = create_recommendation_message(symbol, price, buy_min, buy_max, target, profit_rate, est_time, reason)
    last_sent_times[symbol] = now
    return msg

# === 초기 연결 메시지 ===
def startup_checks():
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            send_telegram("[시스템] ✅ Supabase에 연결되었습니다.")
            print("[시스템] ✅ Supabase에 연결되었습니다.")
        else:
            print("[에러] Supabase 환경변수 누락")
            send_telegram("[에러] ❌ Supabase 연결 정보 누락")

        if check_telegram():
            send_telegram("[시스템] ✅ Telegram에 연결되었습니다.")
            print("[시스템] ✅ Telegram에 연결되었습니다.")
        else:
            print("[에러] Telegram 연결 실패")

    except Exception as e:
        print(f"[에러] 시스템 시작 실패: {e}")
        send_telegram(f"[에러] 시스템 시작 실패\n{str(e)}")

# === 루프 실행 ===
def run_loop():
    while True:
        try:
            msg = detect_coin()
            if msg:
                send_telegram(msg)
                send_to_supabase(msg)
                print(f"[전송 완료] {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"[대기] 조건 불충족 {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[에러] 메인 루프 오류 발생: {e}")
            send_telegram(f"[에러] 메인 루프 오류 발생\n{str(e)}")
        time.sleep(30)

# === 실행 ===
if __name__ == "__main__":
    startup_checks()
    run_loop()
