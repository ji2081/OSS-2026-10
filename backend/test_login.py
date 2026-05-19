import requests
import os
from dotenv import load_dotenv

load_dotenv()

# .env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY가 있어야 합니다!
SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
headers = {"apikey": ANON_KEY}
# 1단계에서 만든 이메일과 비밀번호를 넣으세요
data = {
    "email": "test@dondabazza.com", 
    "password": "password123!"
}

response = requests.post(login_url, headers=headers, json=data)

if response.status_code == 200:
    token = response.json().get("access_token")
    print("🎉 로그인 성공! 아래의 엄청나게 긴 텍스트가 바로 'JWT 토큰'입니다.\n")
    print(token)
else:
    print("❌ 로그인 실패:", response.text)