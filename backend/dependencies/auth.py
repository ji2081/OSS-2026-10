from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

import os
import time
import requests
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gzcadtiiroufqywlsjsz.supabase.co")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

_JWKS_TTL_SECONDS = 86_400  # 24시간

_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0.0


def get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache is None or (now - _jwks_fetched_at) > _JWKS_TTL_SECONDS:
        try:
            resp = requests.get(JWKS_URL, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
        except Exception as e:
            if _jwks_cache is not None:
                return _jwks_cache
            raise RuntimeError(f"JWKS 로드 실패: {e}")
    return _jwks_cache


def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
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
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return UUID(user_id)

    except JWTError as e:
        print(f"[AUTH] JWT 오류: {e}")
        raise credentials_exception