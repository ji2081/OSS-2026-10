from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

app = FastAPI()

#.env 파일 등에서 읽어온 환경 변수 (Docker가 주입해 줌)
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 연결 엔진 생성
engine = create_engine(DATABASE_URL)

@app.get("/test-db")
def test_db_connection():
    try:
        # DB에 간단한 쿼리(SELECT 1)를 보내 연결이 정상인지 확인합니다.
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "success", "message": "Supabase DB 연결 완벽하게 성공!"}
    except Exception as e:
        return {"status": "error", "message": f"연결 실패: {str(e)}"}

@app.get("/")
def read_root():
    return {"message": "OSS-2026-10 백엔드 서버"}