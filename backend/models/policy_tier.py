from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid

class PolicyTier(Base):
    __tablename__ = "policy_tiers2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"))
    max_income_ratio = Column(Float)
    monthly_benefit = Column(Integer)
    duration_months = Column(Integer)