from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import date
from enum import Enum


class PolicyCategory(str, Enum):
    HOUSING    = "housing"
    FINANCE    = "finance"
    EMPLOYMENT = "employment"
    EDUCATION  = "education"
    HEALTH     = "health"
    CULTURE    = "culture"
    WELFARE    = "welfare"
    STARTUP    = "startup"


class PolicyType(str, Enum):
    SUBSIDY          = "subsidy"
    LOAN             = "loan"
    SAVINGS          = "savings"
    VOUCHER          = "voucher"
    INTEREST_SUBSIDY = "interest_subsidy"
    GOODS            = "goods"
    CASHBACK         = "cashback"
    PASS             = "pass"
    OTHER            = "other"


class PolicySchema(BaseModel):
    title:                   str             = Field(..., min_length=2, max_length=200)
    category:                PolicyCategory
    benefit_type:            PolicyType
    host_org:                Optional[str]   = Field(default=None, max_length=100)
    super_region:            str             = Field(default="전국", max_length=50)
    sub_region:              Optional[str]   = Field(default=None, max_length=50)
    age_min:                 Optional[int]   = Field(default=None, ge=0, le=100)
    age_max:                 Optional[int]   = Field(default=None, ge=0, le=100)
    income_standard:         Optional[float] = Field(default=None, ge=0, le=500)
    income_limit:            Optional[int]   = Field(default=None, ge=0)
    total_benefit:           Optional[int]   = Field(default=None, ge=0, le=500_000_000)
    benefit_duration_months: Optional[int]   = Field(default=None, ge=0, le=600)
    benefit_description:     Optional[str]   = Field(default=None, max_length=500)
    apply_start:             Optional[date]  = None
    apply_end:               Optional[date]  = None
    is_active:               bool            = True
    target_unemployed_only:  bool            = False
    exclusive_with:          list[str]       = Field(default_factory=list)
    source_url:              Optional[str]   = Field(default=None, max_length=1000)
    confidence:              float           = Field(default=1.0, ge=0.0, le=1.0)
    raw_data:                Optional[str]   = None

    @field_validator("title")
    @classmethod
    def title_strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("정책명은 비어 있을 수 없습니다.")
        return v.strip()

    @field_validator("age_min", "age_max", mode="before")
    @classmethod
    def clamp_age(cls, v):
        if v is None:
            return None
        if isinstance(v, int) and v > 100:
            return None
        return v

    @field_validator("benefit_duration_months", mode="before")
    @classmethod
    def clamp_duration(cls, v):
        if v is None:
            return None
        if isinstance(v, int) and v > 600:
            return None
        return v

    @field_validator("total_benefit", mode="before")
    @classmethod
    def clamp_benefit(cls, v):
        if v is None:
            return None
        if isinstance(v, int) and v > 500_000_000:
            return None
        return v

    @model_validator(mode="after")
    def age_range_valid(self) -> "PolicySchema":
        if self.age_min is not None and self.age_max is not None:
            if self.age_min > self.age_max:
                raise ValueError(f"age_min({self.age_min}) > age_max({self.age_max})")
        return self

    @model_validator(mode="after")
    def date_range_valid(self) -> "PolicySchema":
        if self.apply_start and self.apply_end:
            if self.apply_start > self.apply_end:
                raise ValueError("apply_start가 apply_end보다 늦습니다.")
        return self

    @model_validator(mode="after")
    def benefit_required(self) -> "PolicySchema":
        if self.total_benefit is None and self.benefit_description is None:
            raise ValueError("total_benefit 또는 benefit_description 중 하나는 필수입니다.")
        return self

    @model_validator(mode="after")
    def set_is_active(self) -> "PolicySchema":
        from datetime import date as date_type
        if self.apply_end is not None and self.apply_end < date_type.today():
            self.is_active = False
        return self