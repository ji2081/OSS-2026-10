from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import uuid


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String)
    benefit_type = Column(String)
    host_org = Column(String)
    source_url = Column(String)

    super_region = Column(String, index=True)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(Text)
    income_type = Column(String)
    income_threshold = Column(Float)
    income_threshold_min = Column(Float)
    parent_income_threshold = Column(Float)

    target_unemployed_only = Column(Boolean, default=False, index=True)
    situational_condition = Column(Text)
    benefit_description = Column(Text)
    benefit_start_lag_days = Column(Integer, default=0)

    apply_start = Column(Date)
    apply_end = Column(Date)
    is_open_ended = Column(Boolean, default=False)

    exclusive_with = Column(JSONB, default=list)
    exclusive_scope = Column(String, default="lifetime")

    is_supplementary = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    confidence = Column(Float, default=1.0)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tiers = relationship("PolicyTier", back_populates="policy", cascade="all, delete-orphan")


class PolicyTier(Base):
    __tablename__ = "policy_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    max_income_ratio = Column(Float)
    monthly_benefit = Column(BigInteger)
    duration_months = Column(Integer)

    policy = relationship("Policy", back_populates="tiers")