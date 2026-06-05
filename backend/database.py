from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DB_DSN")
if not DATABASE_URL:
    raise RuntimeError("DB_DSN 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

# PgBouncer 트랜잭션 모드 호환 설정
# - pool_pre_ping: 체크아웃 시 죽은 커넥션 자동 감지 및 교체
# - pool_reset_on_return: 반환 시 ROLLBACK 실행 (세션 상태 초기화)
# asyncpg로 마이그레이션 시 connect_args={"statement_cache_size": 0} 추가 필요
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