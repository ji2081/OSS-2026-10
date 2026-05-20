from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    total_benefit = Column(BigInteger, nullable=False, default=0)
    policy_count = Column(Integer, nullable=False, default=0)
    algorithm = Column(String, nullable=False)
    exec_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("Policy", secondary="result_policies", backref="optimization_results", overlaps="policy")
    profile = relationship("UserProfile", backref="optimization_results")