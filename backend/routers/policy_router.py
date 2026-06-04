from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import Integer
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import date
from uuid import UUID
import time

from schemas.policy_schema import PolicyResponse, PolicyCategory
from schemas.profile_schema import OptimizeRequest, OptimizeResponse, TimelineItem
from database import get_db
from models.policy import Policy
from models.user_profile import UserProfile
from models.optimization_result import OptimizationResult
from models.result_policy import ResultPolicy

from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("/", response_model=List[PolicyResponse])
def get_policies(
    category: Optional[PolicyCategory] = Query(None),
    super_region: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Policy).options(joinedload(Policy.tiers))

    if category:
        query = query.filter(Policy.category == category.value)
    if super_region:
        query = query.filter(Policy.super_region == super_region)

    return query.offset(skip).limit(limit).all()


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(policy_id: UUID, db: Session = Depends(get_db)):
    policy = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.id == policy_id)
        .first()
    )
    if not policy:
        raise HTTPException(status_code=404, detail=f"정책 ID {policy_id}를 찾을 수 없습니다.")
    return policy


def _calc_end_date(start: date, income_level: Optional[float], policy: Policy) -> date:
    applicable_tier = None
    if policy.tiers:
        if income_level is not None:
            applicable_tier = next(
                (t for t in sorted(policy.tiers, key=lambda t: t.max_income_ratio or 999)
                 if t.max_income_ratio is None or t.max_income_ratio >= income_level),
                policy.tiers[0]
            )
        else:
            applicable_tier = policy.tiers[0]

    if applicable_tier and applicable_tier.duration_months:
        m = start.month - 1 + applicable_tier.duration_months
        return date(start.year + m // 12, m % 12 + 1, 1)

    return date(start.year + 1, start.month, 1)


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_policies(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
):
    current_user_id = UUID("00000000-0000-0000-0000-000000000001")

    age = request.profile.age
    income_level = request.profile.income_level

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user_id).first()
    if not profile:
        profile = UserProfile(
            user_id=current_user_id,
            age=request.profile.age,
            income_level=request.profile.income_level,
            region=request.profile.region,
            is_employed=request.profile.is_employed,
        )
        db.add(profile)
        db.flush()

    base_query = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.is_active == True)
        .filter((Policy.age_min == None) | (Policy.age_min <= age))
        .filter((Policy.age_max == None) | (Policy.age_max >= age))
    )

    if request.profile.is_employed:
        base_query = base_query.filter(Policy.target_unemployed_only == False)

    if income_level is not None:
        base_query = base_query.filter(
            (Policy.income_threshold == None) | (Policy.income_threshold >= income_level)
        )

    if request.profile.region:
        base_query = base_query.filter(
            (Policy.super_region == None) |
            (Policy.super_region == "전국") |
            (Policy.super_region == request.profile.region)
        )

    all_policies = base_query.all()
    print(f"[필터링 결과] {len(all_policies)}개 정책 매칭")

    mwis_candidates = [p for p in all_policies if not p.is_supplementary]
    supplementary = [p for p in all_policies if p.is_supplementary]

    print(f"[MWIS 후보] {len(mwis_candidates)}개")
    for p in mwis_candidates:
        print(f"  - {p.title}")

    if not mwis_candidates:
        return OptimizeResponse(
            total_benefit=0,
            selected_policies=[],
            supplementary_policies=[PolicyResponse.model_validate(p) for p in supplementary],
            timeline=[],
        )

    adjacency_list, weights = build_graph(mwis_candidates, income_level=income_level)

    print(f"[그래프 가중치]")
    for pid, w in weights.items():
        policy = next((p for p in mwis_candidates if p.id == pid), None)
        print(f"  - {policy.title if policy else pid}: {w}원")

    print(f"[배타 간선]")
    for pid, neighbors in adjacency_list.items():
        if neighbors:
            policy = next((p for p in mwis_candidates if p.id == pid), None)
            neighbor_titles = [next((p.title for p in mwis_candidates if p.id == n), str(n)) for n in neighbors]
            print(f"  - {policy.title if policy else pid} ↔ {neighbor_titles}")

    start_time = time.time()
    solver = BruteForceSolver()
    result = solver.solve(adjacency_list, weights)
    exec_ms = int((time.time() - start_time) * 1000)

    selected_set = frozenset(result.selected_ids)
    optimized_policies = [p for p in mwis_candidates if p.id in selected_set]
    unselected_policies = [p for p in mwis_candidates if p.id not in selected_set]

    print(f"[MWIS 선택 결과] total_benefit={result.total_benefit}")
    for p in optimized_policies:
        print(f"  - {p.title} weight={weights.get(p.id, 0)}")

    timeline = []
    for p in optimized_policies:
        start = p.apply_start or date.today()
        end = _calc_end_date(start, income_level, p)
        timeline.append(TimelineItem(
            policy_id=p.id,
            title=p.title,
            start_date=start,
            end_date=end,
        ))

    opt_result = OptimizationResult(
        user_profile_id=profile.id,
        total_benefit=result.total_benefit,
        policy_count=len(optimized_policies),
        algorithm="stage_c_2_preprocess",
        exec_ms=exec_ms,
    )
    db.add(opt_result)
    db.flush()

    for i, (p, t) in enumerate(zip(optimized_policies, timeline)):
        db.add(ResultPolicy(
            result_id=opt_result.id,
            policy_id=p.id,
            seq_order=i,
            start_date=t.start_date,
            end_date=t.end_date,
        ))

    db.commit()

    return OptimizeResponse(
    total_benefit=result.total_benefit,
    selected_policies=[PolicyResponse.model_validate(p) for p in optimized_policies],
    supplementary_policies=[PolicyResponse.model_validate(p) for p in supplementary + unselected_policies],
    timeline=timeline,
)
