from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List

from database import get_db
from models.optimization_result import OptimizationResult
from models.result_policy import ResultPolicy
from models.user_profile import UserProfile
from dependencies.auth import get_current_user
from schemas.result_schema import OptimizationResultResponse

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("/{user_id}", response_model=List[OptimizationResultResponse])
def get_optimization_results(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")

    results = (
        db.query(OptimizationResult)
        .options(joinedload(OptimizationResult.policies))
        .filter(OptimizationResult.user_profile_id == profile.id)
        .order_by(OptimizationResult.created_at.desc())
        .all()
    )

    return results


@router.get("/detail/{result_id}", response_model=OptimizationResultResponse)
def get_optimization_result_detail(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    result = (
        db.query(OptimizationResult)
        .options(joinedload(OptimizationResult.policies))
        .filter(OptimizationResult.id == result_id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

    profile = db.query(UserProfile).filter(UserProfile.id == result.user_profile_id).first()
    if profile.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    return result


@router.get("/latest", response_model=List[OptimizationResultResponse])
def get_latest_results(
    limit: int = 5,
    db: Session = Depends(get_db),
):
    hardcoded_user_id = UUID("00000000-0000-0000-0000-000000000001")
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == hardcoded_user_id
    ).first()
    if not profile:
        return []

    return (
        db.query(OptimizationResult)
        .filter(OptimizationResult.user_profile_id == profile.id)
        .order_by(OptimizationResult.created_at.desc())
        .limit(limit)
        .all()
    )


@router.delete("/detail/{result_id}", status_code=204)
def delete_optimization_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    result = db.query(OptimizationResult).filter(OptimizationResult.id == result_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

    profile = db.query(UserProfile).filter(UserProfile.id == result.user_profile_id).first()
    if profile.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    db.delete(result)
    db.commit()