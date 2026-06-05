from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user_profile import UserProfile
from schemas.profile_schema import OptimizeRequest
from schemas.roadmap_schema import RoadmapResponse
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.policy_filter import filter_policies
from services.transition.roadmap_planner import plan_full_roadmap

router = APIRouter(prefix="/policies", tags=["roadmap"])

_DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    # TODO: 발표 데모 목적의 임시 고정 UUID.
    #       실제 배포 전 Depends(get_current_user) 로 교체 필요.
    income_level = request.profile.income_level

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == _DEMO_USER_ID
    ).first()
    if not profile:
        profile = UserProfile(
            user_id=_DEMO_USER_ID,
            age=request.profile.age,
            income_level=income_level,
            region=request.profile.region,
            is_employed=request.profile.is_employed,
        )
        db.add(profile)
        db.flush()

    mwis_candidates, _ = filter_policies(db, request.profile)

    if not mwis_candidates:
        raise HTTPException(status_code=404, detail="조건에 맞는 정책이 없습니다.")

    adjacency, weights = build_graph(mwis_candidates, income_level=income_level)
    mwis_result = DPDFSSolver().solve(adjacency, weights)

    roadmap = plan_full_roadmap(
        all_mwis_policies=mwis_candidates,
        mwis_ids=set(mwis_result.selected_ids),
        user_start=date.today(),
        income_level=income_level,
        gap_days=14,
        horizon_months=60,
    )

    return RoadmapResponse.from_roadmap(roadmap)