"""
graph_builder.py
================

청년 정책 맞춤형 추천 서비스의 MWIS(Maximum Weight Independent Set) 파이프라인
가장 앞단에 위치하는 '그래프 변환기' 모듈.

DB(SQLAlchemy)에서 조회한 ``Policy`` 객체 리스트를 입력받아,
이후 모든 MWIS 전략(Strategy Pattern)이 공통으로 소비할 수 있는
순수 자료구조(인접 리스트 + 가중치 딕셔너리)로 변환한다.

핵심 책임(invariant)
--------------------
1. **무방향 그래프 보장**:
   ``exclusive_with`` 데이터는 운영 과정에서 단방향으로만 기록되는
   경우가 빈번하다. (A.exclusive_with = [B] 인데 B.exclusive_with = [] 인 상황)
   MWIS 알고리즘은 그래프가 무방향(대칭)이라는 전제 위에서 동작하므로,
   이 모듈에서 단 한 번 정규화하여 (A↔B) 양방향 간선을 강제한다.
   하위 전략들은 이 불변식을 신뢰하고 정규화를 재수행하지 않는다.

2. **고립 노드 보존**:
   배타 조건이 전혀 없는 정책도 독립 집합(independent set)의
   유효한 후보다. 따라서 간선이 없더라도 인접 리스트에 빈 집합으로
   반드시 등록되어야 한다. (그래프에서 누락되면 MWIS 후보에서 탈락됨)

3. **댕글링 참조(dangling reference) 무시**:
   ``exclusive_with`` 가 현재 정책 집합에 존재하지 않는 UUID
   (예: 비활성/삭제된 정책, 사용자 필터링으로 제외된 정책)를
   가리키는 경우, 해당 간선은 그래프에 추가하지 않는다.
   존재하지 않는 노드와의 간선은 MWIS 계산에서 의미가 없으며
   오히려 인덱스 오류의 원인이 된다.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Protocol, runtime_checkable
from uuid import UUID

__all__ = ["PolicyLike", "build_graph"]


# ---------------------------------------------------------------------------
# 타입 계약 (Type Contract)
# ---------------------------------------------------------------------------
#
# 실제 런타임에서는 SQLAlchemy 의 ``Policy`` ORM 모델이 주입되지만,
# 이 모듈은 그래프 변환이라는 단일 책임만 가지므로 ORM 에 직접 의존하지
# 않는다. 대신 "필요한 속성만" 명시한 구조적 타입(Protocol)을 정의한다.
#
# 이렇게 하면:
#   - 단위 테스트에서 가벼운 더미 객체/dataclass 로 대체 가능 (DB 불필요)
#   - 향후 Policy 모델이 변경되어도 그래프 빌더는 영향 없음 (느슨한 결합)
#
@runtime_checkable
class PolicyLike(Protocol):
    """그래프 변환에 필요한 정책의 최소 속성 집합.

    Attributes
    ----------
    id:
        정책의 고유 식별자. SQLAlchemy 모델에서는 ``UUID(as_uuid=True)``
        이므로 런타임 타입은 :class:`uuid.UUID` 다. 노드의 키로 사용된다.
    total_benefit:
        해당 정책 수혜 시 받을 수 있는 총 지원 금액. MWIS 의 가중치(weight).
        DB 컬럼이 nullable 이므로 ``None`` 이 들어올 수 있다.
    exclusive_with:
        중복 수혜가 불가능한(배타적인) 대상 정책 id 들의 컬렉션.
        JSONB 특성상 ``None``, 빈 리스트, 또는 문자열/UUID 가 섞인
        리스트일 수 있다. 정규화는 :func:`build_graph` 가 담당한다.
    """

    id: UUID
    total_benefit: int | None
    exclusive_with: list[str] | None


# 반환 타입 별칭 — 시그니처 가독성 및 하위 전략과의 계약 명시용.
AdjacencyList = dict[UUID, set[UUID]]
Weights = dict[UUID, int]
Graph = tuple[AdjacencyList, Weights]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------
def _coerce_uuid(value: object) -> UUID | None:
    """배타 조건 원소를 :class:`uuid.UUID` 로 안전하게 변환한다.

    ``exclusive_with`` 는 JSONB 컬럼이라 직렬화/역직렬화 경로에 따라
    원소가 ``str`` 일 수도, 이미 :class:`uuid.UUID` 일 수도 있다.
    형식이 깨진 값(잘못된 문자열 등)은 그래프를 오염시키지 않도록
    조용히 ``None`` 을 반환하여 호출부에서 건너뛰게 한다.

    Parameters
    ----------
    value:
        ``exclusive_with`` 리스트의 개별 원소.

    Returns
    -------
    UUID | None
        변환에 성공하면 UUID, 실패하면 ``None``.
    """
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            # 유효하지 않은 UUID 문자열 — 데이터 정합성 문제이지만
            # 그래프 빌더는 방어적으로 무시한다.
            return None
    # int, None, dict 등 예상치 못한 타입은 모두 무시.
    return None


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------
def build_graph(policies: Iterable[PolicyLike]) -> Graph:
    """정책 리스트를 MWIS 입력용 무방향 그래프로 변환한다.

    그래프의 **노드**는 정책 ``id``, **간선**은 두 정책 간 배타(중복 수혜
    불가) 관계, **가중치**는 정책의 ``total_benefit`` 이다.

    이 함수는 다음 불변식을 보장한다.

    1. *대칭성*: 입력 ``exclusive_with`` 가 단방향이어도 반환되는
       인접 리스트는 항상 양방향(무방향 그래프)이다.
    2. *완전성*: 입력된 모든 정책은 간선 유무와 무관하게 인접 리스트와
       가중치 딕셔너리에 키로 존재한다. (고립 노드 보존)
    3. *건전성*: 자기 자신을 가리키는 self-loop, 현재 집합에 없는
       정책을 가리키는 dangling 간선은 모두 제거된다.

    Parameters
    ----------
    policies:
        ``Policy`` ORM 객체(또는 :class:`PolicyLike` 를 만족하는 객체)의
        이터러블. 한 번만 순회 가능한 제너레이터도 안전하게 처리한다.

    Returns
    -------
    tuple[dict[UUID, set[UUID]], dict[UUID, int]]
        ``(adjacency_list, weights)`` 튜플.

        - ``adjacency_list``: ``{정책_id: {배타_관계_정책_id, ...}}``
        - ``weights``: ``{정책_id: total_benefit}``

    Notes
    -----
    - 가중치가 ``None`` 인 정책(컬럼 nullable)은 금액 미정으로 간주하여
      ``0`` 으로 정규화한다. MWIS 에서 가중치 0 노드는 선택해도
      목적함수를 증가시키지 않으므로 안전하게 무해(無害)하다.
    - 동일 ``id`` 가 중복 입력되면 마지막 항목의 가중치가 적용되고
      배타 관계는 합집합으로 병합된다(멱등적·누적적 처리).
    """
    # 인접 리스트. defaultdict(set) 으로 중복 간선을 자동 제거한다.
    adjacency: AdjacencyList = defaultdict(set)
    weights: Weights = {}

    # ── 1단계: 노드 등록 ────────────────────────────────────────────────
    # 간선을 추가하기 전에 모든 유효 노드를 먼저 등록한다. 이렇게 하면
    #   (a) dangling 참조를 판별할 '유효 노드 집합' 확보
    #   (b) 고립 노드가 인접 리스트에 누락되지 않음
    # 두 가지를 동시에 달성한다. (단일 순회를 위해 raw 관계는 임시 저장)
    raw_exclusions: list[tuple[UUID, list[object]]] = []

    for policy in policies:
        node_id = policy.id

        # 가중치: nullable 컬럼이므로 None → 0 으로 정규화.
        weights[node_id] = policy.total_benefit or 0

        # 고립 노드 보존: 키를 명시적으로 '터치'하여 빈 집합 생성.
        _ = adjacency[node_id]

        # JSONB 가 None 이거나 비-리스트일 가능성까지 방어.
        exclusive = policy.exclusive_with
        if exclusive:
            raw_exclusions.append((node_id, list(exclusive)))

    # 이 시점에서 adjacency 의 키 집합 = '현재 그래프에 존재하는 모든 노드'.
    valid_nodes: frozenset[UUID] = frozenset(adjacency.keys())

    # ── 2단계: 간선 추가 (대칭성 강제) ──────────────────────────────────
    for source_id, targets in raw_exclusions:
        for raw_target in targets:
            target_id = _coerce_uuid(raw_target)

            # 변환 실패 / 자기 자신(self-loop) / dangling 참조는 스킵.
            if target_id is None:
                continue
            if target_id == source_id:
                continue
            if target_id not in valid_nodes:
                continue

            # ★ 핵심: 단방향 입력이라도 양쪽 모두에 간선을 추가하여
            #   무방향 그래프 불변식을 강제한다. (A↔B)
            adjacency[source_id].add(target_id)
            adjacency[target_id].add(source_id)

    # 외부로는 일반 dict 로 변환해 반환한다. defaultdict 를 그대로 노출하면
    # 하위 전략에서 존재하지 않는 키 조회 시 의도치 않게 빈 집합이
    # 생성되어 버그를 은폐할 수 있기 때문이다(KeyError 가 정상 동작).
    return dict(adjacency), weights
