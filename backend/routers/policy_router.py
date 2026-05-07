from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from uuid import UUID

from schemas.policy_schema import PolicyResponse, PolicyCategory
from schemas.profile_schema import OptimizeRequest, OptimizeResponse, TimelineItem
from database import get_db
from models import Policy

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
    print(f"소득: {request.profile.income}")
    print(f"미취업 여부: {request.profile.is_unemployed}")
    print(f"지역: {request.profile.super_region} / {request.profile.sub_region}")
    print(f"최소 신뢰도: {request.min_confidence}")
    print("=" * 60)

    # TODO: 실제 MWIS 알고리즘 적용
    policies = db.query(Policy).limit(2).all()

    dummy_response = OptimizeResponse(
        total_benefit=13800000,
        selected_policies=[PolicyResponse.model_validate(p) for p in policies],
        timeline=[
            TimelineItem(
                policy_id=policies[0].id,
                title=policies[0].title,
                start_date=date(2026, 5, 1),
                end_date=date(2026, 10, 31)
            ),
            TimelineItem(
                policy_id=policies[1].id,
                title=policies[1].title,
                start_date=date(2026, 11, 1),
                end_date=date(2027, 4, 30)
            )
        ] if len(policies) >= 2 else []
    )

    return dummy_response