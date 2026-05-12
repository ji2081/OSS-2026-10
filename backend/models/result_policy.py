from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base

class ResultPolicy(Base):
    __tablename__ = "result_policies"

    # 식별자
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 연결 키 
    result_id = Column(UUID(as_uuid=True), ForeignKey("optimization_results.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    
    # 타임라인 및 순서 정보 
    seq_order = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    
    # 관계 설정
    policy = relationship("Policy")