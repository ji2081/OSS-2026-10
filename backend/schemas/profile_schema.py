from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date
from uuid import UUID


class UserProfileRequest(BaseModel):
    age: int = Field(..., ge=0, le=120, description="사용자 나이")
    
    # ※ 비즈니스 요구사항 변경 시: int로 변경 가능  (대부분 정책은 정수 단위 기준 사용)
    income: Optional[float] = Field(None, ge=0.0, description="가구 소득 (중위소득 %, 단위: %)")
    is_unemployed: bool = Field(True, description="미취업 여부")
    super_region: str = Field(..., description="광역 지역 (예: 서울특별시)")
    sub_region: Optional[str] = Field(None, description="기초 지역 (예: 강남구)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 25,
                "income": 80.5,
                "is_unemployed": True,
                "super_region": "서울특별시",
                "sub_region": "강남구"
            }
        }
    )


class OptimizeRequest(BaseModel):
    profile: UserProfileRequest
    # ※ 신뢰도 값 0.5으로 설정. 이후 QA하면서 조율 가능.
    min_confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="최소 신뢰도 필터")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile": {
                    "age": 25,
                    "income": 80.5,
                    "is_unemployed": True,
                    "super_region": "서울특별시",
                    "sub_region": "강남구"
                },
                "min_confidence": 0.7
            }
        }
    )


class TimelineItem(BaseModel):
    """간트 차트 UI를 위한 타임라인 아이템"""
    policy_id: UUID = Field(..., description="정책 고유 ID")
    title: str = Field(..., description="정책명")
    start_date: date = Field(..., description="수혜 시작일")
    end_date: date = Field(..., description="수혜 종료일")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "청년내일저축계좌",
                "start_date": "2026-05-01",
                "end_date": "2026-10-31"
            }
        }
    )


class OptimizeResponse(BaseModel):
    """최적화 추천 API 응답"""
    total_benefit: int = Field(..., description="선택된 정책들의 총 혜택 금액 (원)")
    selected_policies: List["PolicyResponse"] = Field(..., description="선택된 정책 상세 리스트")
    timeline: List[TimelineItem] = Field(..., description="수혜 타임라인 (간트 차트용)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_benefit": 13800000,
                "selected_policies": [],
                "timeline": [
                    {
                        "policy_id": 1,
                        "title": "청년내일저축계좌",
                        "start_date": "2026-05-01",
                        "end_date": "2026-10-31"
                    },
                    {
                        "policy_id": 4,
                        "title": "청년 취업 성공패키지",
                        "start_date": "2026-11-01",
                        "end_date": "2027-04-30"
                    }
                ]
            }
        }
    )


# PolicyResponse 순환 참조 해결
from schemas.policy_schema import PolicyResponse
OptimizeResponse.model_rebuild()