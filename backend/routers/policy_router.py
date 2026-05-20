from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from uuid import UUID

from schemas.policy_schema import PolicyResponse, PolicyCategory
from schemas.profile_schema import OptimizeRequest, OptimizeResponse, TimelineItem
from database import get_db
from models import Policy

from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("/", response_model=List[PolicyResponse])
def get_policies(
    category: Optional[PolicyCategory] = Query(None, description="정책 카테고리 필터"),
    super_region: Optional[str] = Query(None, description="광역 지역 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, ge=1, le=100, description="가져올 최대 항목 수"),
    db: Session = Depends(get_db)
):
    query = db.query(Policy)

    if category:
        query = query.filter(Policy.category == category.value)
    if super_region:
        query = query.filter(Policy.super_region == super_region)

    return query.offset(skip).limit(limit).all()


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(policy_id: UUID, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"정책 ID {policy_id}를 찾을 수 없습니다."
        )

    return policy


@router.post("/optimize", response_model=OptimizeResponse)
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
    query = db.query(Policy).filter(Policy.confidence >= request.min_confidence)

    # 2. 활성 정책만
    query = query.filter(Policy.is_active == True)

    # 3. 나이 필터
    age = request.profile.age
    query = query.filter(
        (Policy.age_min == None) | (Policy.age_min <= age)
    ).filter(
        (Policy.age_max == None) | (Policy.age_max >= age)
    )

    # 4. 미취업 필터 — 미취업자 전용 정책은 미취업자만
    if not request.profile.is_employed:
        query = query.filter(Policy.target_unemployed_only == False)

    policies = query.all()

    print(f"[필터링 결과] {len(policies)}개 정책 매칭")

    # ---------------------------------------------------------------------
    # [수정 구간 시작] 알고리즘 이식
    # ---------------------------------------------------------------------
    
    # 엣지 케이스 방어: 조건에 맞는 정책이 0개면 즉시 빈 결과 반환
    if not policies:
        return OptimizeResponse(
            total_benefit=0,
            selected_policies=[],
            timeline=[],
        )

    # 1. 그래프 빌더를 통해 알고리즘이 먹을 수 있는 형태로 변환
    adjacency_list, weights = build_graph(policies)

    # 2. 가장 빠른 Stage C 전처리 알고리즘 가동
    solver = PreprocessSolver()
    result = solver.solve(adjacency_list, weights)

    # 3. 전체 매칭 정책 중, 알고리즘이 '최적'이라고 고른 정책 객체들만 필터링
    selected_set = frozenset(result.selected_ids)
    optimized_policies = [p for p in policies if p.id in selected_set]

    # ---------------------------------------------------------------------
    # [수정 구간 끝]
    # ---------------------------------------------------------------------

    # 총 수혜액 (알고리즘이 계산해준 완벽한 최적 금액 사용)
    total = result.total_benefit

    # 타임라인 생성 (최적화된 정책들로만 타임라인 구성!)
    timeline = []
    current_date = date.today()
    for p in optimized_policies:  # policies -> optimized_policies 로 변경
        months = p.benefit_duration_months or 6
        start = p.apply_start or current_date
        end = p.apply_end or date(start.year + (start.month + months - 1) // 12, (start.month + months - 1) % 12 + 1, 1)
        timeline.append(TimelineItem(
            policy_id=p.id,
            title=p.title,
            start_date=start,
            end_date=end,
        ))

    return OptimizeResponse(
        total_benefit=total,
        selected_policies=[PolicyResponse.model_validate(p) for p in optimized_policies], # policies -> optimized_policies 로 변경
        timeline=timeline,
    )