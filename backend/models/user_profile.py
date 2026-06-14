from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    age = Column(Integer, nullable=False)
    region = Column(String, nullable=False, index=True)
    sub_region = Column(String, index=True)

    income_level = Column(Integer)
    parent_income = Column(Integer)
    income_median_ratio = Column(Float)
    is_near_poverty = Column(Boolean, default=False)
    is_basic_recipient = Column(Boolean, default=False)

    is_employed = Column(Boolean, nullable=False, default=False, index=True)
    education_level = Column(String)
    housing_type = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)