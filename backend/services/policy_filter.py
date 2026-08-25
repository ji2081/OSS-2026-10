from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from models.policy import Policy
from schemas.profile_schema import UserProfileRequest


def _passes_condition_tags(policy: Policy, confirmed_tags: dict) -> bool:
    """condition_tags 중 하나라도 사용자가 명시적으로 '아니오'(False)라고
    답했으면 이 정책은 제외한다. 아직 답 안 한 태그(키 자체가 없음)나
    '예'(True)라고 답한 태그는 통과시킨다 — 확인 안 된 조건 때문에 정책을
    무조건 숨기지 않고, 일단 후보에 포함시킨 뒤 "확인 필요"로 표시하는 쪽이
    낫다는 설계 결정(사용자가 아직 정보를 안 줬을 뿐이지 자격이 없다고
    확정된 게 아니므로)."""
    tags = policy.condition_tags or []
    return not any(confirmed_tags.get(tag) is False for tag in tags)


def filter_policies(
    db: Session,
    profile: UserProfileRequest,
    confirmed_tags: Optional[dict] = None,
) -> Tuple[List[Policy], List[Policy]]:
    """프로필 조건으로 정책을 필터링하여 (MWIS 후보, 보조정책) 튜플 반환.

    confirmed_tags: UserProfile.confirmed_tags — {"marital_unmarried": True/False, ...}.
    condition_tags(미혼/장애 등)를 요구하는 정책 중, 사용자가 이미 '아니오'라고
    답한 조건에 걸리는 정책만 여기서 걸러낸다(services/condition_tags.py 참고).
    """
    age = profile.age
    income_level = profile.income_level
    confirmed_tags = confirmed_tags or {}

    query = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.is_active == True)
        .filter((Policy.age_min == None) | (Policy.age_min <= age))
        .filter((Policy.age_max == None) | (Policy.age_max >= age))
    )

    if profile.is_employed:
        query = query.filter(Policy.target_unemployed_only == False)

    if income_level is not None:
        query = query.filter(
            (Policy.income_threshold == None) | (Policy.income_threshold >= income_level)
        ).filter(
            (Policy.income_threshold_min == None) | (Policy.income_threshold_min <= income_level)
        )

    if profile.region:
        query = query.filter(
            (Policy.super_region == None) |
            (Policy.super_region == "전국") |
            (Policy.super_region == profile.region)
        )

    all_policies = [p for p in query.all() if _passes_condition_tags(p, confirmed_tags)]
    mwis_candidates = [p for p in all_policies if not p.is_supplementary]
    supplementary   = [p for p in all_policies if p.is_supplementary]

    return mwis_candidates, supplementary


def pending_tag_questions(policies: List[Policy], confirmed_tags: Optional[dict] = None) -> list[dict]:
    """policies(보통 MWIS 결과 + 보조정책)가 요구하는 condition_tags 중,
    사용자가 아직 확인 안 한 것만 골라 질문 목록으로 반환한다. 후보에 실제로
    걸린 태그만 물어보는 게 핵심 — 정책 전체가 쓰는 태그를 다 물어보지 않는다."""
    from services.condition_tags import get_question  # 순환 임포트 방지용 지연 임포트

    confirmed_tags = confirmed_tags or {}
    seen: dict[str, None] = {}
    for p in policies:
        for tag in (p.condition_tags or []):
            if tag not in confirmed_tags and tag not in seen:
                seen[tag] = None
    return [{"tag": tag, "question": get_question(tag)} for tag in seen]