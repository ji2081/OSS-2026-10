from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date
from uuid import UUID


class UserProfileRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    income_level: Optional[int] = Field(None, ge=0)
    is_employed: bool = Field(False)
    region: str = Field(...)
    sub_region: Optional[str] = Field(None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 25,
                "income_level": 80,
                "is_employed": False,
                "region": "서울특별시",
                "sub_region": "강남구"
            }
        }
    )


class ProfileCreateResponse(BaseModel):
    status: str
    message: str
    profile_id: UUID


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