from __future__ import annotations

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from schemas.profile_schema import UserProfileRequest
from schemas.roadmap_schema import RoadmapResponse
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.policy_filter import filter_policies
from services.transition.roadmap_planner import plan_full_roadmap

router = APIRouter(prefix="/policies", tags=["roadmap"])


class RoadmapRequest(BaseModel):
    profile: UserProfileRequest
    selected_policy_ids: Optional[List[str]] = None


@router.post("/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    request: RoadmapRequest,
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    income_level = request.profile.income_level
    mwis_candidates, _ = filter_policies(db, request.profile)

    if not mwis_candidates:
        raise HTTPException(status_code=404, detail="조건에 맞는 정책이 없습니다.")

    if request.selected_policy_ids:
        mwis_ids = {UUID(pid) for pid in request.selected_policy_ids}
    else:
        adjacency, weights = build_graph(mwis_candidates, income_level=income_level)
        mwis_result = DPDFSSolver().solve(adjacency, weights)
        mwis_ids = set(mwis_result.selected_ids)

    roadmap = plan_full_roadmap(
        all_mwis_policies=mwis_candidates,
        mwis_ids=mwis_ids,
        user_start=date.today(),
        income_level=income_level,
        gap_days=14,
        horizon_months=60,
    )
    return RoadmapResponse.from_roadmap(roadmap)