from fastapi import FastAPI
from sqlalchemy import create_engine, text
from routers.policy_router import router as policy_router
from routers.user_router import router as user_router
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드
# pip install python-dotenv 설치가 필요할 수 있음.
# uvicorn main:app --reload 로 테스트 가능

app = FastAPI(
    title="청년 정책 맞춤형 추천 API",
    description="청년을 위한 최적화된 정책 추천 서비스 (OSS-2026-10)",
    version="0.1.0"
)

# .env 파일 등에서 읽어온 환경 변수 (Docker가 주입해 줌)
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 연결 엔진 생성
engine = create_engine(DATABASE_URL)


@app.get("/test-db")
def test_db_connection():
    """Supabase DB 연결 테스트"""
    try:
        # DB에 간단한 쿼리(SELECT 1)를 보내 연결이 정상인지 확인.
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "success", "message": "Supabase DB 연결 완벽하게 성공!"}
    except Exception as e:
        return {"status": "error", "message": f"연결 실패: {str(e)}"}


@app.get("/")
def read_root():
    """루트 엔드포인트"""
    return {
        "message": "OSS-2026-10 백엔드 서버",
        "docs": "/docs",
        "version": "0.1.0"
    }


# 라우터 등록
app.include_router(policy_router)
app.include_router(user_router)


"""
테스트 가능한 엔드포인트

# 서버 상태 확인
GET /

# DB 연결 테스트
GET /test-db

# 정책 목록 조회
GET /policies

# 정책 상세 조회
GET /policies/1

# 최적화 추천
POST /policies/optimize

# 프로필 생성
POST /profiles

"""