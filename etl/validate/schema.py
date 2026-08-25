"""
ETL이 만들어내는 정책 데이터의 검증 스키마.

이전 버전은 policies 테이블이 total_benefit/income_limit/benefit_duration_months/
sub_region 같은 "단일값" 컬럼을 갖고 있던 시절 기준으로 작성되어 있었다. 그 뒤
백엔드는 소득 구간별로 실수혜액이 달라지는 걸 표현하기 위해 policy_tiers
테이블(구간별 max_income_ratio/monthly_benefit/duration_months)로 리팩토링됐는데
(services/mwis/graph_builder.py, models/policy.py 참고) ETL 쪽은 그 변화를
반영하지 못한 채 옛 스키마에 멈춰 있었다. 이 파일은 지금 실제 models/policy.py·
models/policy.py의 PolicyTier와 1:1로 맞춘 버전이다.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import date
from enum import Enum

# backend/schemas/policy_schema.py의 PolicyCategory/PolicyType과 동일한 값 집합을
# 유지한다 — 여기서 갈라지면 프론트 카테고리 필터가 ETL이 넣은 값을 못 알아본다.


class PolicyCategory(str, Enum):
    HOUSING     = "housing"
    FINANCE     = "finance"
    EMPLOYMENT  = "employment"
    EDUCATION   = "education"
    HEALTH      = "health"
    CULTURE     = "culture"
    WELFARE     = "welfare"
    STARTUP     = "startup"
    MILITARY    = "military"
    RIGHTS      = "rights"
    SCHOLARSHIP = "scholarship"


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
    TRAINING         = "training"


# backend/services/condition_tags.py의 CONDITION_TAGS 키와 반드시 같은
# 집합을 유지해야 한다. etl/과 backend/는 별도 실행 루트(각각 프로젝트
# 루트 / backend 디렉터리)라서 import로 공유하기보다 카테고리 enum처럼
# 값만 복제하는 기존 관례를 따른다.
_VALID_CONDITION_TAGS = frozenset({
    "marital_unmarried", "disability_required", "multicultural_family",
    "single_parent", "multi_child_household", "veteran_or_family",
    "certification_holder", "dependent_household_member",
})


class IncomeType(str, Enum):
    MEDIAN_PCT    = "median_pct"     # "기준 중위소득 150% 이하" 같은 비율 기준
    ANNUAL_SALARY = "annual_salary"  # "연 소득 3,600만원 이하" 같은 절대 금액 기준
    NONE          = "none"           # 소득 무관


class PolicyTierSchema(BaseModel):
    """소득 구간 하나에 대한 실수혜액. 구간이 없는(=전원 동일 지원) 정책은
    tiers 배열에 max_income_ratio=None인 항목 하나만 넣는다."""

    max_income_ratio: Optional[float] = Field(default=None, ge=0, le=500)
    monthly_benefit:  int             = Field(..., ge=0, le=50_000_000)
    duration_months:  int             = Field(..., ge=0, le=600)


class PolicySchema(BaseModel):
    title:    str          = Field(..., min_length=2, max_length=200)
    category: PolicyCategory
    benefit_type: PolicyType
    host_org: Optional[str] = Field(default=None, max_length=100)
    super_region: str       = Field(default="전국", max_length=50)

    age_min: Optional[int] = Field(default=None, ge=0, le=100)
    age_max: Optional[int] = Field(default=None, ge=0, le=100)

    income_type:              IncomeType      = IncomeType.NONE
    income_standard:          Optional[str]   = Field(default=None, max_length=500)
    income_threshold:         Optional[float] = Field(default=None, ge=0)  # 상한
    income_threshold_min:     Optional[float] = Field(default=None, ge=0)  # 하한(있는 경우만)
    parent_income_threshold:  Optional[float] = Field(default=None, ge=0)  # 부모 소득 기준(있는 경우만)

    target_unemployed_only: bool = False
    situational_condition:  Optional[str] = Field(default=None, max_length=1000)
    benefit_description:    Optional[str] = Field(default=None, max_length=1000)

    benefit_start_lag_days: int  = Field(default=0, ge=0, le=365)
    apply_start: Optional[date] = None
    apply_end:   Optional[date] = None
    is_open_ended: bool = False

    # LLM은 UUID를 알 수 없으므로 정책명 그대로 채운다. 승격 시점에
    # etl/promote.py의 _resolve_exclusive_with()가 title -> UUID로 보정한다.
    exclusive_with: list[str] = Field(default_factory=list)
    exclusive_scope: str = Field(default="lifetime")

    # 미혼/장애 등 하드 필터로 못 거르는 조건. backend/services/condition_tags.py의
    # 고정 어휘집에 있는 것만 허용 — 목록에 없는 값은 조용히 버린다(정책 자체를
    # 폐기하지 않기 위해. 반복되면 어휘집에 태그를 추가하면 됨).
    condition_tags: list[str] = Field(default_factory=list)

    # True면 MWIS 최적화 대상에서 빠지고 "알짜배기 정보"로만 노출된다.
    # 배타 관계가 없고 소득과 무관하게 소액을 직접 현금으로 주는 정책
    # (예: 자격증 응시료 지원)은 반드시 False로 분류해야 MWIS가 "항상 선택"
    # 처리해준다 — 서비스형/비금전형 혜택만 True.
    is_supplementary: bool = False
    is_active: bool = True

    source_url: Optional[str] = Field(default=None, max_length=1000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    tiers: list[PolicyTierSchema] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def title_strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("정책명은 비어 있을 수 없습니다.")
        return v.strip()

    @field_validator("age_min", "age_max", mode="before")
    @classmethod
    def clamp_age(cls, v):
        if isinstance(v, int) and v > 100:
            return None
        return v

    @field_validator("condition_tags", mode="before")
    @classmethod
    def drop_unknown_condition_tags(cls, v):
        if not v:
            return []
        return [tag for tag in v if tag in _VALID_CONDITION_TAGS]

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
        # 실수혜액(tiers) 또는 최소한 설명 텍스트 중 하나는 있어야
        # MWIS든 알짜배기 목록이든 사용자에게 보여줄 의미가 있다.
        if not self.tiers and self.benefit_description is None:
            raise ValueError("tiers 또는 benefit_description 중 하나는 필수입니다.")
        return self

    @model_validator(mode="after")
    def set_is_active(self) -> "PolicySchema":
        from datetime import date as date_type
        if self.apply_end is not None and self.apply_end < date_type.today() and not self.is_open_ended:
            self.is_active = False
        return self
