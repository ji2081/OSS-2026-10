from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Protocol, runtime_checkable, Optional
from uuid import UUID

__all__ = ["PolicyLike", "build_graph"]


@runtime_checkable
class TierLike(Protocol):
    max_income_ratio: float | None
    monthly_benefit: int | None
    duration_months: int | None


@runtime_checkable
class PolicyLike(Protocol):
    id: UUID
    exclusive_with: list[str] | None
    tiers: list[TierLike]


AdjacencyList = dict[UUID, set[UUID]]
Weights = dict[UUID, int]
Graph = tuple[AdjacencyList, Weights]


def _coerce_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def _calc_weight(tiers: list[TierLike], income_level: Optional[int]) -> int:
    if not tiers:
        return 0

    if income_level is not None:
        applicable = next(
            (t for t in sorted(tiers, key=lambda t: t.max_income_ratio or 999)
             if t.max_income_ratio is None or t.max_income_ratio >= income_level),
            tiers[0]
        )
    else:
        applicable = tiers[0]

    monthly = applicable.monthly_benefit or 0
    months = applicable.duration_months or 0
    return monthly * months


def build_graph(policies: Iterable[PolicyLike], income_level: Optional[int] = None) -> Graph:
    adjacency: AdjacencyList = defaultdict(set)
    weights: Weights = {}
    raw_exclusions: list[tuple[UUID, list[object]]] = []

    for policy in policies:
        node_id = policy.id
        weights[node_id] = _calc_weight(policy.tiers, income_level)
        _ = adjacency[node_id]

        exclusive = policy.exclusive_with
        if exclusive:
            raw_exclusions.append((node_id, list(exclusive)))

    valid_nodes: frozenset[UUID] = frozenset(adjacency.keys())

    for source_id, targets in raw_exclusions:
        for raw_target in targets:
            target_id = _coerce_uuid(raw_target)
            if target_id is None or target_id == source_id or target_id not in valid_nodes:
                continue
            adjacency[source_id].add(target_id)
            adjacency[target_id].add(source_id)

    return dict(adjacency), weights