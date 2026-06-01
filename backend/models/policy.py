from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import uuid


class Policy(Base):
    __tablename__ = "policies2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String)
    benefit_type = Column(String)
    host_org = Column(String)

    super_region = Column(String, nullable=False, index=True)
    sub_region = Column(String)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(String)
    income_limit = Column(Float)
    target_unemployed_only = Column(Boolean, default=False, index=True)

    benefit_description = Column(Text)
    apply_start = Column(Date)
    apply_end = Column(Date)

    exclusive_with = Column(JSONB, default=list)
    source_url = Column(String)
    is_supplementary = Column(Boolean, default=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tiers = relationship("PolicyTier", back_populates="policy", cascade="all, delete-orphan")


class PolicyTier(Base):
    __tablename__ = "policy_tiers2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies2.id", ondelete="CASCADE"), nullable=False)
    max_income_ratio = Column(Float)
    monthly_benefit = Column(BigInteger)
    duration_months = Column(Integer)

    policy = relationship("Policy", back_populates="tiers")
