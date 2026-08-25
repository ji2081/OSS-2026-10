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
    confirmed_tags: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PendingTagQuestion(BaseModel):
    tag: str
    question: str


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
    # 결과에 낀 정책 중 미혼/장애 등 아직 확인 안 된 조건이 있으면 여기 담김.
    # 비어있지 않으면 프론트가 "확인 필요" 배지 + 후속 질문을 보여줘야 함.
    pending_questions: List[PendingTagQuestion] = Field(default_factory=list)

from schemas.policy_schema import PolicyResponse
OptimizeResponse.model_rebuild()