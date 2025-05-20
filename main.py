from datetime import datetime
import os
from supabase import create_client
from postgrest.exceptions import APIError

print("[환경변수 디버깅]")
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_key:
    raise Exception("환경변수 SUPABASE_KEY가 코드에서 감지되지 않음")

supabase = create_client(supabase_url, supabase_key)

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
