from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from database import Base

class ETLLog(Base):
    __tablename__ = "etl_logs" 

    # 식별자 및 실행 시간
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False) 
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False) 
    
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, index=True)

    # 데이터 처리 Funnel 지표
    total_extracted = Column(Integer, default=0)
    total_inserted = Column(Integer, default=0)
    total_skipped = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)

    # 에러 상세 기록 및 생성일
    errors = Column(JSONB, default=list) 
    created_at = Column(DateTime, default=datetime.utcnow)