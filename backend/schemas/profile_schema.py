from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date
from uuid import UUID

# 모델(DB)의 이름과 일치하도록 수정
class UserProfileRequest(BaseModel):
    age: int = Field(..., ge=0, le=120, description="사용자 나이")
    income_level: Optional[int] = Field(None, ge=0.0, description="가구 소득 (중위소득 %, 단위: %)")
    is_employed: bool = Field(False, description="취업 여부 (미취업이 기본값이면 False)")
    region: str = Field(..., description="광역 지역 (예: 서울특별시)")
    sub_region: Optional[str] = Field(None, description="기초 지역 (예: 강남구)")

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
    min_confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="최소 신뢰도 필터")

class TimelineItem(BaseModel):
    policy_id: UUID = Field(..., description="정책 고유 ID")
    title: str = Field(..., description="정책명")
    start_date: date = Field(..., description="수혜 시작일")
    end_date: date = Field(..., description="수혜 종료일")

class OptimizeResponse(BaseModel):
    total_benefit: int = Field(..., description="선택된 정책들의 총 혜택 금액 (원)")
    selected_policies: List["PolicyResponse"] = Field(..., description="선택된 정책 상세 리스트")
    timeline: List[TimelineItem] = Field(..., description="수혜 타임라인 (간트 차트용)")

# PolicyResponse 순환 참조 해결
from schemas.policy_schema import PolicyResponse
OptimizeResponse.model_rebuild()