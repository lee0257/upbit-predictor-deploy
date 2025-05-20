
from datetime import datetime
from postgrest.exceptions import APIError
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_supabase_status():
    try:
        now = datetime.now().isoformat()
        content = f"서버 상태 정상 (시간: {now})"
        response = supabase.table("messages").insert({
            "content": content,
            "created_at": now
        }).execute()
        print("[✅ Supabase 삽입 성공]")
        print(response)
    except APIError as e:
        print("[❌ Supabase 삽입 실패 - APIError]")
        try:
            print("에러 메시지:", e.message)
            print("에러 응답:", e.response.text)
        except Exception:
            print("에러 상세 추출 실패 - 빈 에러 응답")
    except Exception as e:
        print("[❌ Supabase 삽입 실패 - 일반 예외]")
        print(str(e))

if __name__ == "__main__":
    log_supabase_status()
