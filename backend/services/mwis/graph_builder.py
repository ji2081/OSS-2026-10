from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Iterable, Protocol, runtime_checkable, Optional
from uuid import UUID

from services.mwis.tier_resolver import TierLike, resolve_tier

__all__ = ["PolicyLike", "build_graph", "current_window"]

# 가중치/수혜기간을 계산하는 창(window)의 길이. 예전엔 WINDOW_START/END를
# 특정 연도(예: 2026-01-01~12-31)로 하드코딩해서 매년 초 사람이 직접 갱신해야
# 했고, 깜빡하면 연말 이후 모든 weight가 0이 되는 위험이 있었다(backend_check.py
# 3/7에서 수동 점검하던 항목). 지금은 "오늘부터 N개월"로 매번 새로 계산해서
# 이 유지보수 부담 자체를 없앴다 — 과거 정책 데이터를 더 모으는 것과는 별개
# 문제로, is_active=False인 정책은 policy_filter.py에서 이미 걸러지므로 이
# window에 도달하지도 않는다.
HORIZON_MONTHS = 12


def current_window(today: datetime.date | None = None) -> "BenefitPeriod":
    """오늘(today)부터 HORIZON_MONTHS개월 뒤까지의 (window_start, window_end)를 반환한다.

    매 호출마다 새로 계산하므로(모듈 로드 시점에 고정되지 않음) 서버가
    몇 달째 재시작 없이 떠 있어도 window가 그대로 오늘 기준으로 굴러간다.
    """
    start = today or datetime.date.today()
    end = _add_months(start, HORIZON_MONTHS) - datetime.timedelta(days=1)
    return start, end


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


def _benefit_period(policy: PolicyLike, tier: TierLike, window_start: datetime.date) -> BenefitPeriod | None:
    duration = tier.duration_months or 0
    if duration == 0:
        return None

    if policy.is_open_ended:
        raw_start = window_start
    elif policy.apply_start:
        raw_start = policy.apply_start
    else:
        raw_start = window_start

    start = raw_start + datetime.timedelta(days=policy.benefit_start_lag_days)
    end = _add_months(start, duration) - datetime.timedelta(days=1)
    return start, end


def _overlap_months(period: BenefitPeriod, window_start: datetime.date, window_end: datetime.date) -> int:
    start = max(period[0], window_start)
    end = min(period[1], window_end)
    if start >= end:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month)


def _periods_overlap(a: BenefitPeriod, b: BenefitPeriod) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def build_graph(
    policies: Iterable[PolicyLike],
    income_level: Optional[float] = None
) -> Graph:
    window_start, window_end = current_window()

    adjacency: AdjacencyList = defaultdict(set)
    weights: Weights = {}
    periods: dict[UUID, BenefitPeriod | None] = {}
    raw_exclusions: list[tuple[UUID, list[object]]] = []

    for policy in policies:
        node_id = policy.id
        tier = resolve_tier(policy.tiers, income_level)

        if tier is None:
            weights[node_id] = 0
            periods[node_id] = None
        else:
            period = _benefit_period(policy, tier, window_start)
            periods[node_id] = period
            weights[node_id] = (
                (tier.monthly_benefit or 0) * _overlap_months(period, window_start, window_end)
                if period else 0
            )

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