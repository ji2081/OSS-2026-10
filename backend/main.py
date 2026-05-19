from fastapi import FastAPI
from sqlalchemy import text
from routers.policy_router import router as policy_router
from routers.user_router import router as user_router
from database import engine
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path="../.env")

app = FastAPI(
    title="청년 정책 맞춤형 추천 API",
    description="청년을 위한 최적화된 정책 추천 서비스 (OSS-2026-10)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test-db")
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "success", "message": "Supabase DB 연결 완벽하게 성공!"}
    except Exception as e:
        return {"status": "error", "message": f"연결 실패: {str(e)}"}


@app.get("/")
def read_root():
    return {
        "message": "OSS-2026-10 백엔드 서버",
        "docs": "/docs",
        "version": "0.1.0"
    }


app.include_router(policy_router)
app.include_router(user_router)