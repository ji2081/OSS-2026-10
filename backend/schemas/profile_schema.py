from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


class UserProfileRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    income_level: Optional[float] = Field(None, ge=0)  # 중위소득 비율 (예: 0.8 = 80%)
    is_employed: bool = Field(False)
    region: str = Field(...)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 25,
                "income_level": 0.8,
                "is_employed": False,
                "region": "서울"
            }
        }
    )


class ProfileCreateResponse(BaseModel):
    status: str
    message: str
    profile_id: UUID


class UserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    age: int
    income_level: Optional[float] = None
    is_employed: bool
    region: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OptimizeRequest(BaseModel):
    profile: UserProfileRequest


class TimelineItem(BaseModel):
    policy_id: UUID
    title: str
    start_date: date
    end_date: date


class OptimizeResponse(BaseModel):
    total_benefit: int
    selected_policies: List["PolicyResponse"]
    supplementary_policies: List["PolicyResponse"]
    timeline: List[TimelineItem]

from schemas.policy_schema import PolicyResponse
OptimizeResponse.model_rebuild()