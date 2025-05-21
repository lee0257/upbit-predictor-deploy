import requests
from datetime import datetime
import pytz
from supabase import create_client, Client

# ✅ Supabase 정보 (신규 프로젝트)
SUPABASE_URL = "https://btqzlyzwlcbrxyqsmvwo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0cXpseXp3bGNicnh5cXNtdndvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgzMDEzMzUsImV4cCI6MjA2Mzg1NzMzNX0._zDwz1lmGbbgUdOCTl0JhEuFHV1Yf-zm-FomN9mG3s8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 텔레그램 정보
BOT_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
CHAT_IDS = ["1901931119"]
KOREAN_NAME = "카이토"  # 예시

# ✅ 실전 조건 분석 결과 (예시)
coin = {
    "symbol": "KAITO",
    "korean_name": KOREAN_NAME,
    "current_price": 3043,
    "buy_price_min": 3037,
    "buy_price_max": 3043,
    "target_price": 3057,
    "expected_profit": 5,
    "expected_minutes": 10,
    "reason": "체결량 급증 + 매수 강세 포착"
}

# ✅ 텍스트 포맷 생성
def generate_message(c):
    return f"""[추천코인1]
- 코인명: {c['korean_name']} ({c['symbol']})
- 현재가: {c['current_price']:,}원
- 매수 추천가: {c['buy_price_min']:,} ~ {c['buy_price_max']:,}원
- 목표 매도가: {c['target_price']:,}원
- 예상 수익률: 약 {c['expected_profit']}%
- 예상 소요 시간: {c['expected_minutes']}분 이내
- 추천 이유: {c['reason']}
[선행급등포착] 📈

{datetime.now(pytz.timezone("Asia/Seoul")).strftime('%Y-%m-%d')}
"""

TEXT = generate_message(coin)

# ✅ 텔레그램 전송
def send_telegram_message(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, data=data)
        print("[텔레그램 응답]", response.text)

# ✅ Supabase 저장
def save_to_supabase(text):
    now = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    try:
        response = supabase.table("messages").insert({"content": text, "timestamp": now}).execute()
        print("[DB 저장 성공]", response)
    except Exception as e:
        print("[DB 저장 실패]", e)

# ✅ 메인 실행
if __name__ == "__main__":
    print("▶ 실행 시작 - 전체 로직 동작")
    send_telegram_message(TEXT)
    save_to_supabase(TEXT)
    print("▶ 완료")
