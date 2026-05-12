from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    # 식별자
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 연결 정보
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    # 핵심 결과 데이터
    total_benefit = Column(BigInteger, nullable=False, default=0)
    policy_count = Column(Integer, nullable=False, default=0)

    # 알고리즘 성능 및 분석 데이터
    algorithm = Column(String, nullable=False)
    exec_ms = Column(Integer, nullable=False)

    # 생성 시점
    created_at = Column(DateTime, default=datetime.utcnow)

    # 정책 관계 설정 (결과 정책 모델과 연결)
    policies = relationship("Policy", secondary="result_policies", backref="optimization_results")
    # 사용자 프로필 정보 관계 (사용자 프로필 모델과 연결)
    profile = relationship("UserProfile", backref="optimization_results")