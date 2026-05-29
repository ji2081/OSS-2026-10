from fastapi import APIRouter, HTTPException, Query, Depends
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
from dependencies.auth import get_current_user

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


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_policies(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    age = request.profile.age
    income_level = request.profile.income_level

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 먼저 등록해 주세요.")

    base_query = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.is_active == True)
        .filter((Policy.age_min == None) | (Policy.age_min <= age))
        .filter((Policy.age_max == None) | (Policy.age_max >= age))
    )

    if request.profile.is_employed:
        base_query = base_query.filter(Policy.target_unemployed_only == False)

    all_policies = base_query.all()

    mwis_candidates = [p for p in all_policies if not p.is_supplementary]
    supplementary = [p for p in all_policies if p.is_supplementary]

    if not mwis_candidates:
        return OptimizeResponse(
            total_benefit=0,
            selected_policies=[],
            supplementary_policies=[PolicyResponse.model_validate(p) for p in supplementary],
            timeline=[],
        )

    adjacency_list, weights = build_graph(mwis_candidates, income_level=income_level)

    start_time = time.time()
    solver = PreprocessSolver()
    result = solver.solve(adjacency_list, weights)
    exec_ms = int((time.time() - start_time) * 1000)

    selected_set = frozenset(result.selected_ids)
    optimized_policies = [p for p in mwis_candidates if p.id in selected_set]

    timeline = []
    current_date = date.today()
    for p in optimized_policies:
        start = p.apply_start or current_date

        applicable_tier = None
        if income_level and p.tiers:
            applicable_tier = next(
                (t for t in sorted(p.tiers, key=lambda t: t.max_income_ratio or 999)
                 if t.max_income_ratio is None or t.max_income_ratio >= income_level),
                p.tiers[0]
            )

        if p.apply_end:
            end = p.apply_end
        elif applicable_tier and applicable_tier.duration_months:
            end = date(
                start.year + (start.month + applicable_tier.duration_months - 1) // 12,
                (start.month + applicable_tier.duration_months - 1) % 12 + 1,
                1
            )
        else:
            end = date(start.year + 1, start.month, 1)

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
        supplementary_policies=[PolicyResponse.model_validate(p) for p in supplementary],
        timeline=timeline,
    )