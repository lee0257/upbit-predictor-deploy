import os
import requests
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# 환경변수 로드
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 환경변수 검증
print("[환경변수 디버깅]")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY)
print("TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)
print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[❌ Supabase 설정 누락]")
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_text = """
[추천코인1]
- 코인명: DEEP (딥북)
- 현재가: 258원
- 매수 추천가: 254 ~ 259원
- 목표 매도가: 270원
- 예상 수익률: 4.6%
- 예상 소요 시간: 13분
- 추천 이유: 체결량 급증 + 매수 강세 포착
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.KRW-DEEP
""".strip()

        # Supabase 삽입
        data = {
            "message": message_text,
            "timestamp": datetime.now().isoformat()
        }
        supabase.table("messages").insert(data).execute()
        print("[✅ Supabase 삽입 성공]")
    except Exception as e:
        print("[❌ Supabase 삽입 실패]")
        print("에러:", e)

# 텔레그램 전송
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("[⚠️ 텔레그램 설정 누락]")
else:
    try:
        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        send_data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_text
        }
        telegram_res = requests.post(send_url, data=send_data)
        if telegram_res.status_code == 200:
            print("[✅ 텔레그램 메시지 전송 성공]")
        else:
            print("[❌ 텔레그램 전송 실패]")
            print("응답코드:", telegram_res.status_code)
            print("본문:", telegram_res.text)
    except Exception as e:
        print("[❌ 텔레그램 예외 발생]")
        print("에러:", e)
