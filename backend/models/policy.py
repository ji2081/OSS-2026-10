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
<<<<<<< HEAD
    super_region = Column(String)
=======

    super_region = Column(String, nullable=False, index=True)
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65
    sub_region = Column(String)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(String)
    income_limit = Column(Float)
<<<<<<< HEAD
    target_unemployed_only = Column(Boolean, default=False)
    benefit_description = Column(Text)
    apply_start = Column(Date)
    apply_end = Column(Date)
    exclusive_with = Column(JSONB, default=list)
    source_url = Column(String)
    is_active = Column(Boolean, default=True)
    is_supplementary = Column(Boolean, default=False)
    updated_at = Column(DateTime)

    tiers = relationship("PolicyTier", backref="policy", lazy="joined")
=======
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
    __tablename__ = "policy_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    max_income_ratio = Column(Float)
    monthly_benefit = Column(BigInteger)
    duration_months = Column(Integer)

    policy = relationship("Policy", back_populates="tiers")
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65
