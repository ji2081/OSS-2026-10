from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
from database import Base
import uuid

class Policy(Base):
    __tablename__ = "policies"

    # 식별자 및 기본 정보
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    benefit_type = Column(String, nullable=False)
    host_org = Column(String)

    # 지역 및 대상 조건
    super_region = Column(String, nullable=False, index=True)
    sub_region = Column(String)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(Float)
    income_limit = Column(Integer)
    target_unemployed_only = Column(Boolean, default=False, index=True)

    # 혜택 상세 및 일정
    total_benefit = Column(Integer)
    benefit_duration_months = Column(Integer)
    benefit_description = Column(Text)
    apply_start = Column(Date)
    apply_end = Column(Date)

    # 로직 연산 및 데이터 신뢰도
    # 배타 조건은 정책 이름이 아닌 대상 정책의 UUID 문자열 배열로 저장.
    # 데이터 예시: ["uuid-1", "uuid-2"]
    exclusive_with = Column(JSONB, default=list)
    source_url = Column(String)
    confidence = Column(Float, default=1.0)
    raw_data = Column(Text)

    # 관리 상태 및 타임스탬프
    is_active = Column(Boolean, default=True, index=True)
   # created_at = Column(DateTime, default=datetime.utcnow)  # 이 부분 supabase에서 추가필요
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)