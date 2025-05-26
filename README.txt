
[배포 순서 - Fly.io]

1. 이 zip 압축을 GitHub에 올려
2. fly.io에서 이 GitHub 레포 연결
3. 자동으로 배포될 때까지 기다려
4. 배포 후 / 접속 시 {"status": "OK", ...} 나오면 성공
5. /send-message 에서 {"message": "테스트"} POST 전송 → 텔레그램 도착 확인

🔥 Telegram 토큰과 Chat ID는 main.py 하드코딩 상태
