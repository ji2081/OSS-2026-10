from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트(.env)를 이 파일 위치 기준으로 찾는다.
# 이전에는 dotenv_path="../.env" 로 두어 현재 작업 디렉터리에 의존했고,
# backend/ 밖에서 실행하면(예: 루트에서 uvicorn backend.main:app, Docker의
# 다른 WORKDIR) .env를 못 찾아 DB_DSN 오류 발생.
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DB_DSN")
if not DATABASE_URL:
    raise RuntimeError(
        f"DB_DSN 환경 변수가 설정되지 않았습니다. {ENV_PATH} 파일을 확인하세요."
    )

# PgBouncer 트랜잭션 모드 호환 설정
# - pool_pre_ping: 체크아웃 시 죽은 커넥션 자동 감지 및 교체
# - pool_reset_on_return: 반환 시 ROLLBACK 실행 (세션 상태 초기화)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_reset_on_return="rollback",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
