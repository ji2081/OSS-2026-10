from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from schemas.policy_schema import PolicyResponse, PolicyCategory
from schemas.profile_schema import OptimizeRequest, OptimizeResponse, TimelineItem
from database import get_db
from models.policy import Policy
from models.user_profile import UserProfile
from models.optimization_result import OptimizationResult
from models.result_policy import ResultPolicy

from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.policy_filter import filter_policies
from schemas.policy_schema import PolicyResponse, PolicyTierResponse, PolicyCategory

router = APIRouter(prefix="/policies", tags=["Policies"])

_DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _resolve_tier(policy: Policy, income_level: Optional[float]):
    if not policy.tiers:
        return None
    if income_level is None:
        return policy.tiers[0]
    return next(
        (t for t in sorted(policy.tiers, key=lambda t: t.max_income_ratio or 999)
         if t.max_income_ratio is None or t.max_income_ratio >= income_level),
        policy.tiers[0],
    )


def _build_policy_response(p: Policy, income_level: Optional[float]) -> PolicyResponse:
    resp = PolicyResponse.model_validate(p)
    tier = _resolve_tier(p, income_level)
    resp.resolved_tier = PolicyTierResponse.model_validate(tier) if tier else None
    return resp


def _calc_start_date(policy: Policy) -> date:
    lag = policy.benefit_start_lag_days or 0
    return date.today() + timedelta(days=lag)


def _calc_end_date(start: date, income_level: Optional[float], policy: Policy) -> date:
    tier = _resolve_tier(policy, income_level)
    if tier and tier.duration_months:
        total_months = start.month - 1 + tier.duration_months
        return date(start.year + total_months // 12, total_months % 12 + 1, 1)
    return date(start.year + 1, start.month, 1)


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[PolicyResponse])
def get_policies(
    category: Optional[PolicyCategory] = Query(None),
    super_region: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    query = db.query(Policy).options(joinedload(Policy.tiers))
    if category:
        query = query.filter(Policy.category == category.value)
    if super_region:
        query = query.filter(Policy.super_region == super_region)
    return query.offset(skip).limit(limit).all()


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(policy_id: UUID, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    policy = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.id == policy_id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=404, detail=f"정책 ID {policy_id}를 찾을 수 없습니다.")
    return policy


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_policies(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
):
    # TODO: 발표 데모 목적의 임시 고정 UUID.
    #       실제 배포 전 Depends(get_current_user) 로 교체 필요.
    current_user_id = _DEMO_USER_ID
    income_level = request.profile.income_level

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user_id
    ).first()
    if not profile:
        profile = UserProfile(
            user_id=current_user_id,
            age=request.profile.age,
            income_level=income_level,
            region=request.profile.region,
            is_employed=request.profile.is_employed,
        )
        db.add(profile)
        db.flush()

    mwis_candidates, supplementary = filter_policies(db, request.profile)

    print(f"[필터링] 전체 {len(mwis_candidates) + len(supplementary)}개 "
          f"(MWIS 후보: {len(mwis_candidates)}, 보조: {len(supplementary)})")

    if not mwis_candidates:
    return OptimizeResponse(
        total_benefit=0,
        selected_policies=[],
        supplementary_policies=[_build_policy_response(p, income_level) for p in supplementary],
        timeline=[],
    )

    adjacency_list, weights = build_graph(mwis_candidates, income_level=income_level)

    start_ts = time.perf_counter()
    result = DPDFSSolver().solve(adjacency_list, weights)
    exec_ms = int((time.perf_counter() - start_ts) * 1000)

    print(f"[MWIS] total_benefit={result.total_benefit:,}원 "
          f"| 재귀={result.recursion_count} | {exec_ms}ms")

    selected_set     = frozenset(result.selected_ids)
    optimized        = [p for p in mwis_candidates if p.id in selected_set]
    unselected       = [p for p in mwis_candidates if p.id not in selected_set]

    timeline: List[TimelineItem] = []
    for p in optimized:
        start = _calc_start_date(p)
        end   = _calc_end_date(start, income_level, p)
        timeline.append(TimelineItem(
            policy_id=p.id,
            title=p.title,
            start_date=start,
            end_date=end,
        ))

    try:
        opt_result = OptimizationResult(
            user_profile_id=profile.id,
            total_benefit=result.total_benefit,
            policy_count=len(optimized),
            algorithm="stage_b_dp",
            exec_ms=exec_ms,
        )
        db.add(opt_result)
        db.flush()

        for i, (p, t) in enumerate(zip(optimized, timeline)):
            db.add(ResultPolicy(
                result_id=opt_result.id,
                policy_id=p.id,
                seq_order=i,
                start_date=t.start_date,
                end_date=t.end_date,
            ))

        db.commit()
    except Exception:
        db.rollback()
        raise

    return OptimizeResponse(
    total_benefit=result.total_benefit,
    selected_policies=[_build_policy_response(p, income_level) for p in optimized],
    supplementary_policies=[_build_policy_response(p, income_level)
                             for p in supplementary + unselected],
    timeline=timeline,
)
