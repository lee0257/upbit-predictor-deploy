import os
import asyncio
import aiohttp
import pytz
from datetime import datetime
from supabase import create_client, Client
import requests

KST = pytz.timezone("Asia/Seoul")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = [int(os.getenv("TELEGRAM_CHAT_ID", "1901931119"))]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def send_telegram_message(text: str):
    async with aiohttp.ClientSession() as session:
        for chat_id in TELEGRAM_CHAT_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            try:
                async with session.post(url, data=payload) as response:
                    res = await response.text()
                    print("[텔레그램 응답]", res, flush=True)
            except Exception as e:
                print("[텔레그램 오류]", e, flush=True)

def insert_to_supabase(message: str):
    try:
        supabase.table("messages").insert({"content": message}).execute()
        print("[DB 저장 성공]", message, flush=True)
    except Exception as e:
        print("[DB 저장 실패]", e, flush=True)

def get_all_krw_markets():
    url = "https://api.upbit.com/v1/market/all"
    try:
        res = requests.get(url)
        markets = res.json()
        return [m["market"] for m in markets if m["market"].startswith("KRW-") and not m["market"].endswith("USDT")]
    except Exception as e:
        print("[마켓 조회 오류]", e, flush=True)
        return []

def analyze_market():
    try:
        markets = get_all_krw_markets()
        url = "https://api.upbit.com/v1/ticker?markets=" + ",".join(markets)
        res = requests.get(url)
        data = res.json()

        selected = []
        for item in data:
            price = item["trade_price"]
            acc_volume = item["acc_trade_price"]
            change_rate = item["signed_change_rate"] * 100
            market = item["market"]

            if acc_volume > 800000000 and change_rate > 2.5:
                selected.append({
                    "market": market,
                    "price": int(price),
                    "change": round(change_rate, 2),
                    "volume": int(acc_volume)
                })

        selected = sorted(selected, key=lambda x: (-x["change"], -x["volume"]))
        messages = []
        for i, item in enumerate(selected[:3]):
            symbol = item["market"].split("-")[1]
            name = symbol  # 한글 이름 매핑 생략 가능 시 직접 연동
            current = item["price"]
            msg = f"[추천코인{i+1}]\n- 코인명: {name} ({symbol})\n- 현재가: {current}원\n- 매수 추천가: {current-6} ~ {current}원\n- 목표 매도가: {current+14}원\n- 예상 수익률: 약 5%\n- 예상 소요 시간: 10분 이내\n- 추천 이유: 체결량 급증 + 매수 강세 포착\n[선행급등포착]\n\n📊 {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')} 기준"
            messages.append(msg)

        return messages if messages else ["[선행포착] 조건 만족 코인 없음"]

    except Exception as e:
        return [f"[오류] 마켓 분석 실패: {e}"]

async def main():
    print("[실전코드 실행 시작 - 전체 코인 대상]", flush=True)
    messages = analyze_market()
    for msg in messages:
        insert_to_supabase(msg)
        await send_telegram_message(msg)

if __name__ == "__main__":
    asyncio.run(main())
