from typing import List, Tuple

from sqlalchemy.orm import Session, joinedload

from models.policy import Policy
from schemas.profile_schema import UserProfileRequest


def filter_policies(
    db: Session,
    profile: UserProfileRequest,
) -> Tuple[List[Policy], List[Policy]]:
    """프로필 조건으로 정책을 필터링하여 (MWIS 후보, 보조정책) 튜플 반환."""
    age = profile.age
    income_level = profile.income_level

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

    all_policies = query.all()
    mwis_candidates = [p for p in all_policies if not p.is_supplementary]
    supplementary   = [p for p in all_policies if p.is_supplementary]

    return mwis_candidates, supplementary