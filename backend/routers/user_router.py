from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from schemas.profile_schema import UserProfileRequest, ProfileCreateResponse
from database import get_db
from models.user_profile import UserProfile  # 모델 경로 확인 필요
from dependencies.auth import get_current_user # 아까 만든 문지기

router = APIRouter(prefix="/profiles", tags=["Users"])

@router.post("/", response_model=ProfileCreateResponse, status_code=201)
def create_user_profile(
    profile_data: UserProfileRequest, 
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user) # 🛡️ 보안: 로그인한 유저만 가능
):
    """
    [진짜 로직] 로그인한 사용자의 개인 프로필을 DB에 저장합니다.
    """
    try:
        # 1. DB 모델 객체 생성 (로그인한 유저의 ID를 외래키로 연결)
        new_profile = UserProfile(
            user_id=current_user_id, # Supabase에서 가져온 진짜 유저 ID
            age=profile_data.age,
            income=profile_data.income,
            is_unemployed=profile_data.is_unemployed,
            super_region=profile_data.super_region,
            sub_region=profile_data.sub_region
        )
        
        # 2. DB에 저장
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile) # 저장된 후 생성된 UUID 등을 다시 읽어옴
        
        return ProfileCreateResponse(
            status="success",
            message="성공적으로 프로필이 저장되었습니다.",
            profile_id=new_profile.id # 진짜 생성된 UUID 반환
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"프로필 저장 중 오류 발생: {str(e)}")