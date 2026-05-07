from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import date

from schemas.policy_schema import PolicyResponse, PolicyCategory, PolicyType

router = APIRouter(prefix="/policies", tags=["Policies"])


# 더미 데이터 (DB 연동 전 테스트용)
DUMMY_POLICIES = [
    {
        "id": 1,
        "title": "청년내일저축계좌",
        "category": PolicyCategory.FINANCE,
        "benefit_type": PolicyType.SAVINGS,
        "host_org": "보건복지부",
        "super_region": "서울특별시",
        "sub_region": "강남구",
        "age_min": 15,
        "age_max": 40,
        "income_standard": 100.0,
        "income_limit": None,
        "total_benefit": 10800000,
        "benefit_duration_months": 36,
        "benefit_description": "근로활동을 통해 자립을 준비하는 생계·의료급여 수급 가구 청년의 자산형성을 지원합니다.",
        "apply_start": date(2024, 1, 1),
        "apply_end": date(2024, 12, 31),
        "is_active": True,
        "target_unemployed_only": False,
        "exclusive_with": [3],
        "source_url": "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do",
        "confidence": 0.95
    },
    {
        "id": 2,
        "title": "청년 전세임대주택",
        "category": PolicyCategory.HOUSING,
        "benefit_type": PolicyType.SUBSIDY,
        "host_org": "국토교통부",
        "super_region": "서울특별시",
        "sub_region": None,
        "age_min": 19,
        "age_max": 39,
        "income_standard": 100.0,
        "income_limit": None,
        "total_benefit": None,
        "benefit_duration_months": 24,
        "benefit_description": "대학생 및 취업준비생 등 무주택 청년에게 전세임대주택을 지원합니다.",
        "apply_start": date(2024, 3, 1),
        "apply_end": None,
        "is_active": True,
        "target_unemployed_only": False,
        "exclusive_with": [],
        "source_url": "https://www.molit.go.kr",
        "confidence": 0.88
    },
    {
        "id": 3,
        "title": "스타트업 원스톱 지원센터",
        "category": PolicyCategory.STARTUP,
        "benefit_type": PolicyType.OTHER,
        "host_org": "중소벤처기업부",
        "super_region": "전국",
        "sub_region": None,
        "age_min": None,
        "age_max": None,
        "income_standard": None,
        "income_limit": None,
        "total_benefit": None,
        "benefit_duration_months": None,
        "benefit_description": "창업 준비부터 성장까지 원스톱 지원 서비스를 제공합니다.",
        "apply_start": None,
        "apply_end": None,
        "is_active": True,
        "target_unemployed_only": False,
        "exclusive_with": [1],
        "source_url": "https://www.mss.go.kr",
        "confidence": 0.72
    },
    {
        "id": 4,
        "title": "청년 취업 성공패키지",
        "category": PolicyCategory.EMPLOYMENT,
        "benefit_type": PolicyType.SUBSIDY,
        "host_org": "고용노동부",
        "super_region": "경기도",
        "sub_region": "수원시",
        "age_min": 18,
        "age_max": 34,
        "income_standard": 120.0,
        "income_limit": None,
        "total_benefit": 3000000,
        "benefit_duration_months": 12,
        "benefit_description": "청년층 구직자에게 맞춤형 취업지원 프로그램과 취업성공수당을 지급합니다.",
        "apply_start": date(2024, 1, 15),
        "apply_end": date(2024, 12, 15),
        "is_active": True,
        "target_unemployed_only": True,
        "exclusive_with": [],
        "source_url": "https://www.work.go.kr",
        "confidence": 0.91
    }
]


@router.get("/", response_model=List[PolicyResponse])
def get_policies(
    category: Optional[PolicyCategory] = Query(None, description="정책 카테고리 필터"),
    super_region: Optional[str] = Query(None, description="광역 지역 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=1, le=100, description="가져올 최대 항목 수")
):
    """
    정책 목록 조회 (필터링 및 페이징 지원)
    
    - category: 카테고리별 필터링 (housing, finance, employment 등)
    - super_region: 광역 지역별 필터링 (서울특별시, 경기도 등)
    - skip: 페이징을 위한 offset
    - limit: 한 번에 가져올 항목 수 (최대 100)
    """
    filtered_policies = DUMMY_POLICIES
    
    # 카테고리 필터링
    if category:
        filtered_policies = [p for p in filtered_policies if p["category"] == category]
    
    # 광역 지역 필터링
    if super_region:
        filtered_policies = [p for p in filtered_policies if p["super_region"] == super_region]
    
    # 페이징 처리
    paginated_policies = filtered_policies[skip : skip + limit]
    
    return paginated_policies


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(policy_id: int):
    """
    정책 상세 조회
    
    - policy_id: 조회할 정책의 고유 ID
    """
    policy = next((p for p in DUMMY_POLICIES if p["id"] == policy_id), None)
    
    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"정책 ID {policy_id}를 찾을 수 없습니다."
        )
    
    return policy
