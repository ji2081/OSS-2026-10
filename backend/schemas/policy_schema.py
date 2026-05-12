from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional, List
from datetime import date
from uuid import UUID


class PolicyCategory(str, Enum):
    HOUSING = "housing"
    FINANCE = "finance"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    HEALTH = "health"
    CULTURE = "culture"
    WELFARE = "welfare"
    STARTUP = "startup"


class PolicyType(str, Enum):
    SUBSIDY = "subsidy"
    LOAN = "loan"
    SAVINGS = "savings"
    VOUCHER = "voucher"
    INTEREST_SUBSIDY = "interest_subsidy"
    GOODS = "goods"
    CASHBACK = "cashback"
    PASS = "pass"
    OTHER = "other"


class PolicyResponse(BaseModel):
    id: UUID
    title: str
    category: PolicyCategory
    benefit_type: PolicyType
    host_org: Optional[str] = None
    super_region: str
    sub_region: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    income_standard: Optional[float] = None
    income_limit: Optional[int] = None
    total_benefit: Optional[int] = None
    benefit_duration_months: Optional[int] = None
    benefit_description: Optional[str] = None
    apply_start: Optional[date] = None
    apply_end: Optional[date] = None
    is_active: bool = True
    target_unemployed_only: bool = False
    exclusive_with: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI 추천 신뢰도")

    model_config = ConfigDict(from_attributes=True)