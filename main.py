
import os
from supabase import create_client, Client
import telegram
from flask import Flask
import time
from datetime import datetime

# 환경 변수에서 설정 불러오기
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telegram.Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[상태] 서버 작동 중 - {now}"
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    supabase.table("messages").insert({"message": message, "created_at": now}).execute()
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
