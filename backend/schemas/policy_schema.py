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
    SCHOLARSHIP = "scholarship"
    MILITARY = "military"
    RIGHTS = "rights"


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
    TRAINING = "training"


class PolicyTierResponse(BaseModel):
    max_income_ratio: Optional[float] = None
    monthly_benefit: Optional[int] = None
    duration_months: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PolicyResponse(BaseModel):
    id: UUID
    title: str
    category: Optional[PolicyCategory] = None
    benefit_type: Optional[PolicyType] = None
    host_org: Optional[str] = None
    super_region: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    income_standard: Optional[str] = None
    income_threshold: Optional[float] = None
    income_threshold_min: Optional[float] = None
    benefit_description: Optional[str] = None
    apply_start: Optional[date] = None
    apply_end: Optional[date] = None
    is_open_ended: bool = False
    benefit_start_lag_days: int = 0
    is_active: bool = True
    is_supplementary: bool = False
    target_unemployed_only: bool = False
    exclusive_with: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    tiers: List[PolicyTierResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)