import requests
from datetime import datetime
import pytz
from supabase import create_client, Client

# ✅ Supabase 설정 (환경변수 X)
SUPABASE_URL = "https://hqwyfqccghosrgynckhr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhxd3lmcWNjZ2hvc3JneW5ja2hyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgzMDA4NjgsImV4cCI6MjA2Mzg1Njg2OH0.LSRIDJZUZsQRUCPMbBfZWhp95i7Ru3IDZtFqeu5Pr4E"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 텔레그램 설정
BOT_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
CHAT_IDS = ["1901931119"]  # 알림 대상
TEXT = """
[추천코인1]
- 코인명: 카이토 (KAITO)
- 현재가: 3,043원
- 매수 추천가: 3,037 ~ 3,043원
- 목표 매도가: 3,057원
- 예상 수익률: 약 5%
- 예상 소요 시간: 10분 이내
- 추천 이유: 체결량 급증 + 매수 강세 포착
[선행급등포착] 📈

2025-05-21
"""

# ✅ 메시지 전송
def send_telegram_message(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, data=data)
        print("[텔레그램 응답]", response.text)

# ✅ Supabase 저장
def save_to_supabase(text):
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        response = supabase.table("messages").insert({"content": text, "timestamp": timestamp}).execute()
        print("[DB 저장 성공]", response)
    except Exception as e:
        print("[DB 저장 실패]", e)

# ✅ 실행
if __name__ == "__main__":
    print("▶ 실행 시작 - 전체 로직 동작")
    send_telegram_message(TEXT)
    save_to_supabase(TEXT)
    print("▶ 완료")
