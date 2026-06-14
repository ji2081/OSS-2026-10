from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Iterable, Protocol, runtime_checkable, Optional
from uuid import UUID

__all__ = ["PolicyLike", "build_graph"]

# 가중치/수혜기간 계산 기준 연도. 매년 초 갱신 필요 (지나면 weight=0 위험, backend_check.py 3/7에서 점검)
WINDOW_START = datetime.date(2026, 1, 1)
WINDOW_END = datetime.date(2026, 12, 31)


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
    apply_start: datetime.date | None
    benefit_start_lag_days: int
    is_open_ended: bool


AdjacencyList = dict[UUID, set[UUID]]
Weights = dict[UUID, int]
BenefitPeriod = tuple[datetime.date, datetime.date]
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


def _add_months(d: datetime.date, months: int) -> datetime.date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return datetime.date(year, month, 1)


def _get_tier(tiers: list[TierLike], income_level: Optional[float]) -> TierLike | None:
    if not tiers:
        return None
    if income_level is not None:
        return next(
            (t for t in sorted(tiers, key=lambda t: t.max_income_ratio or 999)
             if t.max_income_ratio is None or t.max_income_ratio >= income_level),
            tiers[0]
        )
    return tiers[0]


def _benefit_period(policy: PolicyLike, tier: TierLike) -> BenefitPeriod | None:
    duration = tier.duration_months or 0
    if duration == 0:
        return None

    if policy.is_open_ended:
        raw_start = WINDOW_START
    elif policy.apply_start:
        raw_start = policy.apply_start
    else:
        raw_start = WINDOW_START

    start = raw_start + datetime.timedelta(days=policy.benefit_start_lag_days)
    end = _add_months(start, duration) - datetime.timedelta(days=1)
    return start, end


def _overlap_months(period: BenefitPeriod) -> int:
    start = max(period[0], WINDOW_START)
    end = min(period[1], WINDOW_END)
    if start >= end:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month)


def _periods_overlap(a: BenefitPeriod, b: BenefitPeriod) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def build_graph(
    policies: Iterable[PolicyLike],
    income_level: Optional[float] = None
) -> Graph:
    adjacency: AdjacencyList = defaultdict(set)
    weights: Weights = {}
    periods: dict[UUID, BenefitPeriod | None] = {}
    raw_exclusions: list[tuple[UUID, list[object]]] = []

    for policy in policies:
        node_id = policy.id
        tier = _get_tier(policy.tiers, income_level)

        if tier is None:
            weights[node_id] = 0
            periods[node_id] = None
        else:
            period = _benefit_period(policy, tier)
            periods[node_id] = period
            weights[node_id] = (tier.monthly_benefit or 0) * _overlap_months(period) if period else 0

        _ = adjacency[node_id]

        if policy.exclusive_with:
            raw_exclusions.append((node_id, list(policy.exclusive_with)))

    valid_nodes = frozenset(adjacency.keys())

    for source_id, targets in raw_exclusions:
        for raw_target in targets:
            target_id = _coerce_uuid(raw_target)
            if target_id is None or target_id == source_id or target_id not in valid_nodes:
                continue

            # 수혜 기간이 겹치는 경우에만 배타 간선 추가 (환승 허용)
            sp = periods.get(source_id)
            tp = periods.get(target_id)
            if sp and tp and _periods_overlap(sp, tp):
                adjacency[source_id].add(target_id)
                adjacency[target_id].add(source_id)

    return dict(adjacency), weights