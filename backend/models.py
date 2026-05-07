from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from database import Base
import uuid

class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    benefit_type = Column(String, nullable=False)
    host_org = Column(String)
    super_region = Column(String, nullable=False)
    sub_region = Column(String)
    age_min = Column(Integer)
    age_max = Column(Integer)
    income_standard = Column(Float)
    income_limit = Column(Integer)
    total_benefit = Column(Integer)
    benefit_duration_months = Column(Integer)
    benefit_description = Column(Text)
    apply_start = Column(Date)
    apply_end = Column(Date)
    is_active = Column(Boolean, default=True)
    target_unemployed_only = Column(Boolean, default=False)
    exclusive_with = Column(JSONB, default=list)
    source_url = Column(String)
    confidence = Column(Float, default=1.0)