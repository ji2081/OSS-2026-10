from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from schemas.profile_schema import UserProfileRequest, ProfileCreateResponse, UserProfileResponse
from database import get_db
from models.user_profile import UserProfile
from dependencies.auth import get_current_user

router = APIRouter(prefix="/profiles", tags=["Users"])


@router.post("/", response_model=ProfileCreateResponse, status_code=201)
def create_user_profile(
    profile_data: UserProfileRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    try:
        new_profile = UserProfile(
            user_id=current_user_id,
            age=profile_data.age,
            income_level=profile_data.income_level,
            is_employed=profile_data.is_employed,
            region=profile_data.region,
            sub_region=profile_data.sub_region
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return ProfileCreateResponse(
            status="success",
            message="성공적으로 프로필이 저장되었습니다.",
            profile_id=new_profile.id
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"프로필 저장 중 오류 발생: {str(e)}")


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")

    return profile


@router.put("/{user_id}", response_model=UserProfileResponse)
def update_user_profile(
    user_id: UUID,
    profile_data: UserProfileRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다.")

    profile.age = profile_data.age
    profile.income_level = profile_data.income_level
    profile.is_employed = profile_data.is_employed
    profile.region = profile_data.region
    profile.sub_region = profile_data.sub_region

    db.commit()
    db.refresh(profile)

    return profile