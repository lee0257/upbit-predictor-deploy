from fastapi import FastAPI, Request
import requests
import os

# === 🔐 환경 변수 기반 설정값 ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_IDS_RAW = os.environ.get("CHAT_IDS", "")
CHAT_IDS = CHAT_IDS_RAW.split(",") if CHAT_IDS_RAW else []

# === 🚀 FastAPI 앱 시작 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    if not TELEGRAM_TOKEN or not CHAT_IDS:
        print("[오류] TELEGRAM_TOKEN 또는 CHAT_IDS가 설정되지 않음")
        return

    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id.strip(),
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("[텔레그램 응답]", response.status_code, response.text)
            if response.status_code != 200:
                raise Exception("Invalid response from Telegram API")
        except Exception as e:
            print(f"[오류] 텔레그램 전송 실패: {e}")
            raise

# === 🔁 POST: 수동추천 메시지 전송 엔드포인트 ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있습니다"}

    try:
        send_telegram_message(message)
    except Exception:
        return {"status": "fail", "message": "❌ 텔레그램 전송 실패"}

    return {"status": "success", "message": "✅ 텔레그램 전송 완료"}

# === 🌐 GET: URL로 메시지 전송 테스트 ===
@app.get("/send")
def send_get_message(msg: str = "🔥 기본 메시지입니다"):
    try:
        send_telegram_message(msg)
        return {"status": "success", "message": "✅ 텔레그램 전송 완료"}
    except Exception:
        return {"status": "fail", "message": "❌ 전송 실패"}

# === 🟢 서버 상태 확인 ===
@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결되었습니다 ✅"}