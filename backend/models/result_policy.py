from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base

class ResultPolicy(Base):
    __tablename__ = "result_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey("optimization_results.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    seq_order = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)

    policy = relationship("Policy", primaryjoin="ResultPolicy.policy_id == Policy.id", foreign_keys=[policy_id], overlaps="optimization_results,policies")
    result = relationship("OptimizationResult", back_populates="policies")