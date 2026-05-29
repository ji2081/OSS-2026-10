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

def get_total_benefit(policy):
    if not policy.tiers:
        return 0
    tier = policy.tiers[0]
    return (tier.monthly_benefit or 0) * (tier.duration_months or 0)
    

@router.post("/optimize", response_model=OptimizeResponse)
<<<<<<< HEAD
def optimize_policies(request: OptimizeRequest, db: Session = Depends(get_db)):
    print("=" * 60)
    print("[POST /optimize] 요청 수신")
    print(f"나이: {request.profile.age}")
    print(f"소득: {request.profile.income_level}")
    print(f"미취업 여부: {request.profile.is_employed}")
    print(f"지역: {request.profile.region} / {request.profile.sub_region}")
    print(f"최소 신뢰도: {request.min_confidence}")
    print("=" * 60)

    # 1. 신뢰도 필터
    # query = db.query(Policy).filter(Policy.confidence >= request.min_confidence)
    query = db.query(Policy)

    # 2. 활성 정책만
    query = query.filter(Policy.is_active == True)

    # 3. 나이 필터
=======
def optimize_policies(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65
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

<<<<<<< HEAD
    # 4. 미취업 필터 — 미취업자 전용 정책은 미취업자만
    if request.profile.is_employed:
        query = query.filter(Policy.target_unemployed_only == False)
=======
    if request.profile.is_employed:
        base_query = base_query.filter(Policy.target_unemployed_only == False)
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65

    all_policies = base_query.all()

<<<<<<< HEAD
    for p in policies[:3]:
        print(f"{p.title} - monthly: {p.tiers[0].monthly_benefit if p.tiers else None}, duration: {p.tiers[0].duration_months if p.tiers else None}")

    print(f"[필터링 결과] {len(policies)}개 정책 매칭")

    # 총 수혜액 계산
    total = sum(get_total_benefit(p) for p in policies)
=======
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
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65

    timeline = []
    current_date = date.today()
<<<<<<< HEAD
    for p in policies:
        months = p.tiers[0].duration_months if p.tiers else 6
=======
    for p in optimized_policies:
>>>>>>> 63779c2625fa96af55cb5b854ef73a617097dd65
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