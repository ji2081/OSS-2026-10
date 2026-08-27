from __future__ import annotations

import calendar
import datetime
from collections import defaultdict
from typing import Iterable, Protocol, runtime_checkable, Optional
from uuid import UUID

from services.mwis.tier_resolver import TierLike, resolve_tier

__all__ = ["PolicyLike", "build_graph", "current_window"]

# 가중치/수혜기간을 계산하는 창(window)의 길이.
# 오늘부터 N개월로 매번 새로 계산해서 유지보수 부담을 없앰.
# 과거 정책 데이터를 더 모으는 것과는 별개 문제로, is_active=False인 정책은 policy_filter.py에서 이미 걸러짐.
HORIZON_MONTHS = 12


def current_window(today: datetime.date | None = None) -> "BenefitPeriod":
    """오늘(today)부터 HORIZON_MONTHS개월 뒤까지의 (window_start, window_end)를 반환한다.
    매 호출마다 새로 계산하므로 서버가 계속 재시작 없이 떠 있어도 window가 그대로 오늘 기준으로 굴러간다.
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
    """일(day)을 보존하며 개월을 더한다.

    이전 구현은 반환값의 day를 항상 1로 고정해서, 월 중순에 시작하는 정책의
    수혜 기간이 최대 30일까지 짧아졌다(3/15 시작 12개월 -> 2027-02-28 종료).
    대상 월에 해당 일자가 없으면(1/31 + 1개월) 그 달의 마지막 날로 절삭한다.
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


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
    """수혜 기간과 window가 겹치는 개월 수.

    이전 구현은 종료일을 포함 구간으로 두고 (end.month - start.month)만 계산해
    모든 정책이 1개월씩 과소 산정됐다(12개월 정책 -> 11개월). 특히 1개월짜리
    정책은 0이 되어 가중치가 사라지고 MWIS 후보에서 사실상 제외됐다.
    종료일 다음 날을 반개구간 끝으로 삼아 온전히 채운 개월 수를 센다.
    """
    start = max(period[0], window_start)
    end = min(period[1], window_end)
    if start > end:
        return 0

    end_exclusive = end + datetime.timedelta(days=1)
    months = (end_exclusive.year - start.year) * 12 + (end_exclusive.month - start.month)
    if end_exclusive.day < start.day:
        months -= 1
    return max(months, 0)


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
