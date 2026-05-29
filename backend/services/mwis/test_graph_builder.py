"""
test_graph_builder.py
=====================

``backend.services.mwis.graph_builder.build_graph`` 에 대한 단위 테스트.

테스트 철학
-----------
이 모듈은 MWIS 파이프라인의 가장 앞단이므로, 여기서 그래프 불변식이
깨지면 5가지 전략 알고리즘이 모두 잘못된 입력 위에서 동작하게 된다.
따라서 '정상 케이스'보다 '데이터가 더러운 케이스'에 검증을 집중한다.

테스트는 실제 SQLAlchemy/DB 에 의존하지 않는다. ``graph_builder`` 가
구조적 타입(:class:`PolicyLike` Protocol)에만 의존하도록 설계되었으므로,
실제 ``Policy`` 모델의 속성 접근 방식(``policy.id``, ``policy.total_benefit``,
``policy.exclusive_with``)을 그대로 모사한 경량 ``dataclass`` 스텁을 사용한다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from uuid import UUID

import pytest

from backend.services.mwis.graph_builder import build_graph


# ---------------------------------------------------------------------------
# 테스트 픽스처 / 헬퍼
# ---------------------------------------------------------------------------
@dataclass
class FakePolicy:
    """실제 ``Policy`` ORM 모델의 속성 접근 방식을 모사한 테스트 스텁.

    실제 모델과 동일하게 ``id``(UUID), ``total_benefit``(nullable int),
    ``exclusive_with``(nullable list) 속성을 제공한다. Protocol 기반
    설계 덕분에 DB 없이도 동일한 코드 경로를 검증할 수 있다.
    """

    id: UUID
    total_benefit: int | None = 0
    exclusive_with: list[str] | None = field(default=None)


def make_id() -> UUID:
    """결정적 가독성을 위해 UUID 를 생성하는 헬퍼."""
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# 1. 정상 케이스 — 기본 동작
# ---------------------------------------------------------------------------
def test_returns_adjacency_and_weights_tuple() -> None:
    """반환값이 (인접리스트, 가중치) 튜플이고 가중치가 매핑되는지 검증."""
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=1000),
        FakePolicy(id=b, total_benefit=2500),
    ]

    adjacency, weights = build_graph(policies)

    assert isinstance(adjacency, dict)
    assert isinstance(weights, dict)
    assert weights == {a: 1000, b: 2500}
    # 배타 조건이 없으므로 모든 노드는 고립(빈 집합) 상태여야 한다.
    assert adjacency == {a: set(), b: set()}


def test_bidirectional_input_is_preserved() -> None:
    """이미 양방향으로 들어온 배타 조건이 그대로 유지되는지 검증."""
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=500, exclusive_with=[str(b)]),
        FakePolicy(id=b, total_benefit=800, exclusive_with=[str(a)]),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


# ---------------------------------------------------------------------------
# 2. [필수 엣지케이스] 단방향 → 양방향 대칭 변환
# ---------------------------------------------------------------------------
def test_unidirectional_exclusion_becomes_symmetric() -> None:
    """핵심 요구사항: A 만 B 를 배척해도 B 도 A 를 배척하도록 대칭화.

    A.exclusive_with = [B] 이지만 B.exclusive_with 는 비어 있는,
    운영에서 가장 흔한 '단방향 누락' 시나리오를 검증한다.
    """
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=300, exclusive_with=[str(b)]),
        FakePolicy(id=b, total_benefit=400, exclusive_with=None),  # 누락!
    ]

    adjacency, _ = build_graph(policies)

    # A→B 는 명시적으로 존재.
    assert b in adjacency[a]
    # B→A 는 입력에 없었지만 빌더가 강제로 대칭화해야 한다.
    assert a in adjacency[b], "단방향 배타 조건이 양방향으로 정규화되지 않았습니다."


def test_three_node_chain_unidirectional_symmetry() -> None:
    """다중 노드 체인(A→B, B→C)에서도 전 구간 대칭이 보장되는지 검증."""
    a, b, c = make_id(), make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=100, exclusive_with=[str(b)]),
        FakePolicy(id=b, total_benefit=200, exclusive_with=[str(c)]),
        FakePolicy(id=c, total_benefit=300, exclusive_with=[]),  # 빈 리스트
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a, c}  # A 로부터 역방향, C 로 정방향
    assert adjacency[c] == {b}     # B 로부터 역방향 대칭


# ---------------------------------------------------------------------------
# 3. [필수 엣지케이스] 노드가 아예 없는 경우
# ---------------------------------------------------------------------------
def test_empty_policy_list() -> None:
    """빈 입력에 대해 빈 그래프/가중치를 안전하게 반환하는지 검증.

    MWIS 알고리즘이 빈 그래프에서 즉시 0 을 반환할 수 있도록,
    예외 없이 ``({}, {})`` 가 나와야 한다.
    """
    adjacency, weights = build_graph([])

    assert adjacency == {}
    assert weights == {}


def test_empty_generator_input() -> None:
    """일회성 제너레이터(빈 경우)도 안전하게 처리되는지 검증."""
    adjacency, weights = build_graph(p for p in [])

    assert adjacency == {}
    assert weights == {}


# ---------------------------------------------------------------------------
# 4. 데이터 건전성(self-loop / dangling / None)
# ---------------------------------------------------------------------------
def test_self_loop_is_ignored() -> None:
    """정책이 자기 자신을 배척 대상으로 가리키면 그 간선은 제거되어야 한다."""
    a = make_id()
    policies = [FakePolicy(id=a, total_benefit=999, exclusive_with=[str(a)])]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == set(), "self-loop 는 그래프에서 제외되어야 합니다."


def test_dangling_reference_is_ignored() -> None:
    """현재 정책 집합에 없는 id 를 가리키는 간선은 무시되어야 한다.

    (비활성/삭제 정책이나 사용자 필터로 제외된 정책을 가리키는 경우)
    """
    a = make_id()
    ghost = make_id()  # policies 리스트에 포함되지 않은 유령 노드
    policies = [FakePolicy(id=a, total_benefit=100, exclusive_with=[str(ghost)])]

    adjacency, weights = build_graph(policies)

    assert adjacency == {a: set()}
    assert ghost not in adjacency
    assert ghost not in weights


def test_none_total_benefit_is_normalized_to_zero() -> None:
    """nullable 컬럼인 total_benefit 이 None 이면 0 으로 정규화되어야 한다."""
    a = make_id()
    policies = [FakePolicy(id=a, total_benefit=None)]

    _, weights = build_graph(policies)

    assert weights[a] == 0


def test_invalid_uuid_string_in_exclusive_with_is_skipped() -> None:
    """깨진 UUID 문자열이 섞여도 예외 없이 해당 원소만 건너뛰어야 한다."""
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(
            id=a,
            total_benefit=100,
            exclusive_with=["not-a-valid-uuid", str(b)],
        ),
        FakePolicy(id=b, total_benefit=200),
    ]

    adjacency, _ = build_graph(policies)

    # 유효한 b 와의 간선만 살아남고, 깨진 문자열은 무시.
    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


def test_uuid_object_in_exclusive_with_is_accepted() -> None:
    """exclusive_with 원소가 str 이 아닌 UUID 객체여도 정상 처리되어야 한다.

    (JSONB 역직렬화 경로에 따라 원소 타입이 달라질 수 있음)
    """
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=100, exclusive_with=[b]),  # UUID 객체
        FakePolicy(id=b, total_benefit=200),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


# ---------------------------------------------------------------------------
# 5. 중복 입력 / 누적 병합
# ---------------------------------------------------------------------------
def test_duplicate_edges_are_deduplicated() -> None:
    """동일 배타 관계가 양쪽에서 중복 선언돼도 간선은 한 번만 존재."""
    a, b = make_id(), make_id()
    policies = [
        FakePolicy(id=a, total_benefit=100, exclusive_with=[str(b), str(b)]),
        FakePolicy(id=b, total_benefit=200, exclusive_with=[str(a)]),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


def test_returned_adjacency_is_plain_dict_not_defaultdict() -> None:
    """반환된 인접 리스트는 일반 dict 여야 한다.

    defaultdict 를 노출하면 하위 전략에서 존재하지 않는 노드 조회 시
    KeyError 대신 빈 집합이 조용히 생성되어 버그를 은폐할 수 있다.
    """
    a = make_id()
    adjacency, _ = build_graph([FakePolicy(id=a, total_benefit=1)])

    missing = make_id()
    with pytest.raises(KeyError):
        _ = adjacency[missing]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
