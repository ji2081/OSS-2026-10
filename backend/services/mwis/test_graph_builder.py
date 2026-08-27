"""
test_graph_builder.py

graph_builder.build_graph()에 대한 단위 테스트.

이전에는 graph_builder.py가 total_benefit 기반에서 tiers 기반 가중치 계산으로
리팩토링되면서 FakePolicy가 PolicyLike 프로토콜과 맞지 않아 11개가 skip 상태였다.
FakePolicy/FakeTier를 현재 프로토콜에 맞춰 갱신해 전부 복구했다.

가중치가 실행 날짜에 의존하지 않도록, 기간 관련 테스트는 is_open_ended=True로
두어 수혜 기간이 항상 current_window()와 정확히 일치하게 만든다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from uuid import UUID

import pytest

from services.mwis.graph_builder import HORIZON_MONTHS, build_graph


@dataclass
class FakeTier:
    monthly_benefit: int | None = 0
    duration_months: int | None = HORIZON_MONTHS
    max_income_ratio: float | None = None


@dataclass
class FakePolicy:
    id: UUID
    tiers: list[FakeTier] = field(default_factory=lambda: [FakeTier()])
    exclusive_with: list[str] | None = None
    apply_start: object = None
    benefit_start_lag_days: int = 0
    is_open_ended: bool = True


def make_id() -> UUID:
    return uuid.uuid4()


def policy(monthly: int = 0, **kwargs) -> FakePolicy:
    """월 수혜액 monthly, 기간 HORIZON_MONTHS인 정책. 가중치는 monthly * HORIZON_MONTHS."""
    return FakePolicy(id=kwargs.pop("id", make_id()), tiers=[FakeTier(monthly_benefit=monthly)], **kwargs)


def test_returns_adjacency_and_weights_tuple() -> None:
    a, b = make_id(), make_id()
    policies = [policy(id=a, monthly=1000), policy(id=b, monthly=2500)]

    adjacency, weights = build_graph(policies)

    assert isinstance(adjacency, dict)
    assert isinstance(weights, dict)
    assert weights == {a: 1000 * HORIZON_MONTHS, b: 2500 * HORIZON_MONTHS}
    assert adjacency == {a: set(), b: set()}


def test_bidirectional_input_is_preserved() -> None:
    a, b = make_id(), make_id()
    policies = [
        policy(id=a, monthly=500, exclusive_with=[str(b)]),
        policy(id=b, monthly=800, exclusive_with=[str(a)]),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


def test_unidirectional_exclusion_becomes_symmetric() -> None:
    a, b = make_id(), make_id()
    policies = [
        policy(id=a, monthly=300, exclusive_with=[str(b)]),
        policy(id=b, monthly=400, exclusive_with=None),  # 누락
    ]

    adjacency, _ = build_graph(policies)

    assert b in adjacency[a]
    assert a in adjacency[b]


def test_three_node_chain_unidirectional_symmetry() -> None:
    a, b, c = make_id(), make_id(), make_id()
    policies = [
        policy(id=a, monthly=100, exclusive_with=[str(b)]),
        policy(id=b, monthly=200, exclusive_with=[str(c)]),
        policy(id=c, monthly=300, exclusive_with=[]),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a, c}
    assert adjacency[c] == {b}


def test_empty_policy_list() -> None:
    adjacency, weights = build_graph([])

    assert adjacency == {}
    assert weights == {}


def test_empty_generator_input() -> None:
    adjacency, weights = build_graph(p for p in [])

    assert adjacency == {}
    assert weights == {}


def test_self_loop_is_ignored() -> None:
    a = make_id()
    policies = [policy(id=a, monthly=999, exclusive_with=[str(a)])]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == set()


def test_dangling_reference_is_ignored() -> None:
    a, ghost = make_id(), make_id()
    policies = [policy(id=a, monthly=100, exclusive_with=[str(ghost)])]

    adjacency, weights = build_graph(policies)

    assert adjacency == {a: set()}
    assert ghost not in adjacency
    assert ghost not in weights


def test_none_monthly_benefit_is_normalized_to_zero() -> None:
    a = make_id()
    policies = [FakePolicy(id=a, tiers=[FakeTier(monthly_benefit=None)])]

    _, weights = build_graph(policies)

    assert weights[a] == 0


def test_policy_without_tiers_gets_zero_weight() -> None:
    a = make_id()
    policies = [FakePolicy(id=a, tiers=[])]

    adjacency, weights = build_graph(policies)

    assert weights[a] == 0
    assert adjacency[a] == set()


def test_zero_duration_tier_gets_zero_weight() -> None:
    a = make_id()
    policies = [FakePolicy(id=a, tiers=[FakeTier(monthly_benefit=500, duration_months=0)])]

    _, weights = build_graph(policies)

    assert weights[a] == 0


def test_invalid_uuid_string_in_exclusive_with_is_skipped() -> None:
    a, b = make_id(), make_id()
    policies = [
        policy(id=a, monthly=100, exclusive_with=["not-a-valid-uuid", str(b)]),
        policy(id=b, monthly=200),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


def test_uuid_object_in_exclusive_with_is_accepted() -> None:
    a, b = make_id(), make_id()
    policies = [
        policy(id=a, monthly=100, exclusive_with=[b]),
        policy(id=b, monthly=200),
    ]

    adjacency, _ = build_graph(policies)

    assert adjacency[a] == {b}
    assert adjacency[b] == {a}


def test_zero_weight_policy_still_forms_exclusion_edge() -> None:
    """가중치가 0이어도 수혜 기간이 겹치면 배타 간선은 유지된다."""
    a, b = make_id(), make_id()
    policies = [
        policy(id=a, monthly=0, exclusive_with=[str(b)]),
        policy(id=b, monthly=700),
    ]

    adjacency, weights = build_graph(policies)

    assert weights[a] == 0
    assert adjacency[a] == {b}
