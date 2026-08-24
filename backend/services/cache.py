"""아주 단순한 프로세스 메모리 TTL 캐시.

/verify/* 엔드포인트(검증 대시보드용)는 의도적으로 인증 없이 공개되어 있지만
연산량이 크다 — distribution은 최대 2^20개 조합을 직접 enumerate하고,
exhaustive는 704개 프로필 전체를 매번 DB 조회 + 그래프 빌드 + 솔버 실행으로
재계산한다. 정책 데이터가 바뀌지 않는 한 결과는 항상 같으므로, 매 요청마다
다시 계산하는 대신 짧은 TTL로 캐싱해 반복 호출(또는 악의적 연타)로 인한
서버 부하·비용 리스크를 줄인다.

여러 워커/인스턴스로 스케일하면 프로세스별로 캐시가 나뉘어 효과가 줄어드는데,
현재 배포 규모(단일 Railway 인스턴스)에서는 충분하다. 인스턴스가 늘어나면
Redis 등 공유 캐시로 교체가 필요하다.
"""
from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_store: dict[str, tuple[float, Any]] = {}


def cached(key: str, ttl_seconds: float, compute: Callable[[], T]) -> T:
    now = time.time()
    hit = _store.get(key)
    if hit is not None and (now - hit[0]) < ttl_seconds:
        return hit[1]
    value = compute()
    _store[key] = (now, value)
    return value
