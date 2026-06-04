from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.policy import Policy
from models.user_profile import UserProfile
from schemas.profile_schema import OptimizeRequest
from schemas.roadmap_schema import RoadmapResponse
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver
from services.transition.roadmap_planner import plan_full_roadmap

router = APIRouter(prefix="/policies", tags=["roadmap"])

_HARDCODED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    age = request.profile.age
    income_level = request.profile.income_level
    region = request.profile.region
    user_start = date.today()

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == _HARDCODED_USER_ID
    ).first()
    if not profile:
        profile = UserProfile(
            user_id=_HARDCODED_USER_ID,
            age=age,
            income_level=income_level,
            region=region,
            is_employed=request.profile.is_employed,
        )
        db.add(profile)
        db.flush()

    base_q = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.is_active == True)
        .filter((Policy.age_min == None) | (Policy.age_min <= age))
        .filter((Policy.age_max == None) | (Policy.age_max >= age))
    )
    if request.profile.is_employed:
        base_q = base_q.filter(Policy.target_unemployed_only == False)

    if region:
        base_q = base_q.filter(
            (Policy.super_region == None) |
            (Policy.super_region == "전국") |
            (Policy.super_region == region)
        )

    all_policies = base_q.all()
    mwis_candidates = [p for p in all_policies if not p.is_supplementary]

    if not mwis_candidates:
        raise HTTPException(status_code=404, detail="조건에 맞는 정책이 없습니다.")

    adjacency, weights = build_graph(mwis_candidates, income_level=income_level)
    mwis_result = PreprocessSolver().solve(adjacency, weights)

    roadmap = plan_full_roadmap(
        all_mwis_policies=mwis_candidates,
        mwis_ids=set(mwis_result.selected_ids),
        user_start=user_start,
        income_level=income_level,
        gap_days=14,
        horizon_months=60,
    )

    return RoadmapResponse.from_roadmap(roadmap)