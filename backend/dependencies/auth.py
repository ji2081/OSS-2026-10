# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from uuid import UUID

security = HTTPBearer()

# .env에서 시크릿 키 가져오기
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"

def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """헤더의 Bearer 토큰을 검증하고 유저의 UUID를 반환합니다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요한 서비스입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = auth.credentials
        # Supabase 토큰 검증
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM], audience="authenticated")
        user_id: str = payload.get("sub") 
        
        if user_id is None:
            raise credentials_exception
            
        return UUID(user_id)
        
    except JWTError:
        raise credentials_exception