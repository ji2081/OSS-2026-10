from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    # 식별자
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 기본 인적 사항 (필수 조건)
    age = Column(Integer, nullable=False)
    region = Column(String, nullable=False, index=True)
    sub_region = Column(String, index=True)

    # 경제적 조건
    income_level = Column(Integer)
    parent_income = Column(Integer)
    income_median_ratio = Column(Float)
    is_near_poverty = Column(Boolean, default=False)
    is_basic_recipient = Column(Boolean, default=False)

    # 사회적 상태 및 환경
    is_employed = Column(Boolean, nullable=False, default=False, index=True)
    education_level = Column(String)
    housing_type = Column(String)

    # 시스템 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)