import time
import traceback
from datetime import datetime
import requests
from supabase import create_client

# ✅ 서버 및 키 설정
SERVER_NAME = "[업비트-선행포착]"
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"
TELEGRAM_TOKEN = "6343590063:AAH-V0BrkjFDqNV3Im2DdEny_7L9_Km-0uI"
TELEGRAM_CHAT_IDS = [1901931119]  # 수신자 ID, 친구 제외됨

# ✅ Supabase 연결
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 환경 검증
def check_env_keys():
    errors = []

    if not SUPABASE_URL.startswith("https://"):
        errors.append("❌ Supabase URL 형식 오류")

    if not SUPABASE_KEY or len(SUPABASE_KEY) < 30:
        errors.append("❌ Supabase 키 누락 또는 형식 오류")

    if not TELEGRAM_TOKEN or not TELEGRAM_TOKEN.startswith("6"):
        errors.append("❌ 텔레그램 토큰 형식 오류")

    if not TELEGRAM_CHAT_IDS:
        errors.append("❌ 수신 대상(chat_id) 설정 안 됨")

    if errors:
        for err in errors:
            print(err)
        raise ValueError("⛔ 환경변수 설정 오류: 서버 실행 중단")


# ✅ 에러 로그 기록
def log_error(message):
    print(f"[ERROR] {message}")
    try:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {message}\n")
    except:
        pass


# ✅ 텔레그램 전송
def send_telegram(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            res = requests.post(url, json={"chat_id": chat_id, "text": message})
            if res.status_code == 401:
                log_error("❌ 텔레그램 인증 오류 (토큰 문제)")
        except Exception as e:
            log_error(f"텔레그램 전송 실패 ({chat_id}): {e}")


# ✅ Supabase 삽입
def insert_message_to_db(message_dict):
    try:
        response = supabase.table("messages").insert(message_dict).execute()
        if response.status_code in [401, 403]:
            send_telegram("❌ Supabase 인증 오류 발생 (키 만료 또는 권한 부족)")
        elif not (200 <= response.status_code < 300):
            log_error(f"Supabase 삽입 실패: {response}")
    except Exception as e:
        log_error(f"Supabase 삽입 오류: {e}")


# ✅ 상태 메시지
def send_status():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram(f"{SERVER_NAME} 서버 작동 중 ✅\n{now}")


# ✅ 여기에 분석 로직을 추가하면 됨
def run_main_logic():
    try:
        # 예시: 딥북 실전 분석 결과 (선행급등포착)
        coin_data = {
            "coin": "DEEP",
            "signal": "선행급등포착",
            "price": 258,
            "created_at": datetime.now().isoformat()
        }
        insert_message_to_db(coin_data)

        # 텔레그램 메시지 포맷
        message = """
[추천코인1]
- 코인명: DEEP (딥북)
- 현재가: 258원
- 매수 추천가: 255 ~ 259원
- 목표 매도가: 278원
- 예상 수익률: 7.8%
- 예상 소요 시간: 15분
- 추천 이유: 체결량 급증 + 매수세 유입
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.KRW-DEEP
"""
        send_telegram(message)

    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"run_main_logic 오류 발생: {e}\n{tb}")
        send_telegram(f"{SERVER_NAME} 메인 로직 오류 ⚠️\n{e}")


# ✅ 실행
if __name__ == "__main__":
    try:
        check_env_keys()
        print(f"{SERVER_NAME} 서버 실행 중...")
        send_status()

        while True:
            try:
                run_main_logic()
            except Exception as e:
                tb = traceback.format_exc()
                log_error(f"전체 실행 오류: {e}\n{tb}")
                send_telegram(f"{SERVER_NAME} 전체 실행 오류 ⚠️\n{e}")
            time.sleep(60)  # 실행 간격 (초)

    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"서버 시작 실패: {e}\n{tb}")
        send_telegram(f"{SERVER_NAME} 서버 시작 실패 ❌\n{e}")
