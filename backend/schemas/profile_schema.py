from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


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
                "is_unemployed": False,
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
                    "is_unemployed": False,
                    "super_region": "서울특별시",
                    "sub_region": "강남구"
                },
                "min_confidence": 0.7
            }
        }
    )
