from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, DateTime
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
    super_region = Column(String)
    sub_region = Column(String)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(String)
    income_limit = Column(Float)
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