from fastapi import APIRouter
from schemas.profile_schema import UserProfileRequest
from pydantic import BaseModel

router = APIRouter(prefix="/profiles", tags=["Users"])


class ProfileCreateResponse(BaseModel):
    """프로필 생성 응답"""
    status: str
    message: str
    profile_id: int


@router.post("/", response_model=ProfileCreateResponse, status_code=201)
def create_user_profile(profile: UserProfileRequest):
    """
    사용자 프로필 생성
    
    ※ 현재는 더미 로직입니다. (DB 연동 전)
    
    - age: 사용자 나이
    - income: 가구 소득 (중위소득 %)
    - is_unemployed: 미취업 여부
    - super_region: 광역 지역
    - sub_region: 기초 지역
    """
    print("=" * 60)
    print("[POST /profiles] 프로필 생성 요청 수신")
    print("-" * 60)
    print(f"나이: {profile.age}세")
    print(f"소득: {profile.income}% (중위소득 대비)" if profile.income else "소득: 미입력")
    print(f"미취업 여부: {'예' if profile.is_unemployed else '아니오'}")
    print(f"광역 지역: {profile.super_region}")
    print(f"기초 지역: {profile.sub_region if profile.sub_region else '미입력'}")
    print("=" * 60)
    
    # TODO: Supabase DB profiles 테이블에 데이터 INSERT 로직 추가
    # 예시:
    # async with database.session() as session:
    #     new_profile = UserProfile(
    #         age=profile.age,
    #         income=profile.income,
    #         is_unemployed=profile.is_unemployed,
    #         super_region=profile.super_region,
    #         sub_region=profile.sub_region
    #     )
    #     session.add(new_profile)
    #     await session.commit()
    #     await session.refresh(new_profile)
    #     profile_id = new_profile.id
    
    # 더미 응답: 임시 ID 반환
    dummy_profile_id = 1
    
    return ProfileCreateResponse(
        status="success",
        message="프로필이 성공적으로 임시 저장되었습니다 (DB 연동 전)",
        profile_id=dummy_profile_id
    )
