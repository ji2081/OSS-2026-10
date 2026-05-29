# # dependencies/auth.py
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import jwt, JWTError
# import os
# from uuid import UUID
# from dotenv import load_dotenv
# load_dotenv(dotenv_path="../.env")

# security = HTTPBearer()

# # .env에서 시크릿 키 가져오기
# JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# # [추가] 시크릿 키 누락 방지 
# if not JWT_SECRET:
#     raise RuntimeError("SUPABASE_JWT_SECRET 환경 변수가 설정되지 않았습니다! .env 파일을 확인하세요.")

# ALGORITHM = "HS256"

# def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
#     # 헤더의 Bearer 토큰을 검증하고 유저의 UUID를 반환
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="로그인이 필요한 서비스입니다.",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         token = auth.credentials
#         # Supabase 토큰 검증
#         payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
#         user_id: str = payload.get("sub") 
        
#         if user_id is None:
#             raise credentials_exception
            
#         return UUID(user_id)
        
#     except JWTError as e:
#         print(f"JWT 오류: {e}")
#         raise credentials_exception


# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
import requests
from uuid import UUID
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gzcadtiiroufqywlsjsz.supabase.co")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        response = requests.get(JWKS_URL)
        _jwks_cache = response.json()
    return _jwks_cache


def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요한 서비스입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = auth.credentials
        jwks = get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256", "HS256"],
            audience="authenticated"
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        return UUID(user_id)

    except JWTError as e:
        print(f"JWT 오류: {e}")
        raise credentials_exception