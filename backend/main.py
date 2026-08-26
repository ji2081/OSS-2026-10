from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from routers.policy_router import router as policy_router
from routers.user_router import router as user_router
from routers.result_router import router as result_router
from routers.roadmap_router import router as roadmap_router
from routers.verification_router import router as verification_router
from database import engine

app = FastAPI(
    title="청년 정책 맞춤형 추천 API",
    description="청년을 위한 최적화된 정책 추천 서비스 (OSS-2026-10)",
    version="0.1.0"
)

_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

# localhost만 허용하면 휴대폰으로 같은 네트워크의 Mac IP(예: 192.168.x.x:3000)에
# 접속해 테스트할 때 Origin이 안 맞아 CORS preflight(OPTIONS)가 막힌다. 사설 IP
# 대역 + 개발 포트(3000/5173)만 정규식으로 허용해서, IP가 바뀔 때마다 매번
# ALLOWED_ORIGINS를 손으로 안 고쳐도 되게 한다. 외부 인터넷에서는 애초에
# 사설 IP를 Origin으로 주장할 수 없으므로 프로덕션에서도 안전하다.
LOCAL_NETWORK_ORIGIN_REGEX = (
    r"^http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}):(3000|5173)$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=LOCAL_NETWORK_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

@app.get("/")
def read_root():
    return {"message": "OSS-2026-10 백엔드 서버", "docs": "/docs", "version": "0.1.0"}

@app.get("/dashboard")
def verification_dashboard():
    return FileResponse("verify.html")

app.include_router(policy_router)
app.include_router(user_router)
app.include_router(result_router)
app.include_router(roadmap_router)
app.include_router(verification_router)