from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class PolicyInterval:
    policy_id: UUID
    title: str
    category: str
    benefit_start: date
    benefit_end: date
    total_benefit: int
    monthly_benefit: int
    duration_months: int


@dataclass
class RoadmapPhase:
    label: str
    phase_start: date
    phase_end: date
    total_benefit: int
    policies: list[PolicyInterval] = field(default_factory=list)


@dataclass
class FullRoadmap:
    phases: list[RoadmapPhase]
    total_benefit: int
    total_months: int
    transitions: list[tuple[str, str]]


def _resolve_tier(policy, income_level: Optional[float]):
    if not policy.tiers:
        return None
    if income_level is not None:
        return next(
            (t for t in sorted(policy.tiers, key=lambda t: t.max_income_ratio or 999)
             if t.max_income_ratio is None or t.max_income_ratio >= income_level),
            policy.tiers[0],
        )
    return policy.tiers[0]


def _benefit_window(
    policy,
    anchor: date,
    income_level: Optional[float],
) -> tuple[date, date, int, int, int] | None:
    """(benefit_start, benefit_end, total_benefit, duration_months, monthly_benefit)"""
    tier = _resolve_tier(policy, income_level)
    if tier is None or not tier.monthly_benefit or not tier.duration_months:
        return None

    lag = timedelta(days=policy.benefit_start_lag_days or 0)
    start = (policy.apply_start or anchor) + lag
    m = tier.duration_months
    end = date(
        start.year + (start.month + m - 1) // 12,
        (start.month + m - 1) % 12 + 1,
        1,
    )
    return start, end, tier.monthly_benefit * m, m, tier.monthly_benefit


def _lifetime_excluded(all_policies, mwis_ids: set[UUID]) -> set[UUID]:
    excluded: set[UUID] = set()
    for p in all_policies:
        if p.id not in mwis_ids:
            continue
        scope = getattr(p, "exclusive_scope", "lifetime") or "lifetime"
        if scope != "lifetime":
            continue
        raw = p.exclusive_with or []
        if isinstance(raw, str):
            raw = json.loads(raw)
        for eid in raw:
            try:
                excluded.add(UUID(str(eid)))
            except (ValueError, AttributeError):
                pass
    return excluded


def _make_intervals(
    policies,
    after: date,
    income_level: Optional[float],
    horizon: date,
) -> list[PolicyInterval]:
    result = []
    for p in policies:
        w = _benefit_window(p, after, income_level)
        if w is None:
            continue
        bstart, bend, total, months, monthly = w
        if bstart < after or bstart > horizon:
            continue
        result.append(PolicyInterval(
            policy_id=p.id,
            title=p.title,
            category=p.category or "",
            benefit_start=bstart,
            benefit_end=bend,
            total_benefit=total,
            monthly_benefit=monthly,
            duration_months=months,
        ))
    return sorted(result, key=lambda x: x.benefit_start)


def _dag_dp(
    intervals: list[PolicyInterval],
    origin: date,
    gap_days: int,
) -> list[PolicyInterval]:
    if not intervals:
        return []

    n = len(intervals)
    origin_dl = origin + timedelta(days=gap_days)
    dp: list[tuple[int, int]] = [(-1, -1)] * n

    for i, iv in enumerate(intervals):
        if iv.benefit_start <= origin_dl:
            dp[i] = (iv.total_benefit, -1)

    for j in range(n):
        if dp[j][0] < 0:
            continue
        for k in range(j + 1, n):
            if intervals[j].benefit_end + timedelta(days=gap_days) <= intervals[k].benefit_start:
                val = dp[j][0] + intervals[k].total_benefit
                if val > dp[k][0]:
                    dp[k] = (val, j)

    best = max(range(n), key=lambda i: dp[i][0])
    if dp[best][0] < 0:
        return []

    path: list[int] = []
    cur = best
    while cur != -1:
        path.append(cur)
        cur = dp[cur][1]
    path.reverse()
    return [intervals[i] for i in path]


def plan_full_roadmap(
    all_mwis_policies,
    mwis_ids: set[UUID],
    user_start: date,
    income_level: Optional[float] = None,
    gap_days: int = 14,
    horizon_months: int = 60,
) -> FullRoadmap:
    hm = horizon_months
    horizon = date(
        user_start.year + (user_start.month + hm - 1) // 12,
        (user_start.month + hm - 1) % 12 + 1,
        1,
    )

    phase1_ivs: list[PolicyInterval] = []
    phase1_end = user_start

    for p in all_mwis_policies:
        if p.id not in mwis_ids:
            continue
        w = _benefit_window(p, user_start, income_level)
        if w is None:
            continue
        bstart, bend, total, months, monthly = w
        phase1_ivs.append(PolicyInterval(
            policy_id=p.id,
            title=p.title,
            category=p.category or "",
            benefit_start=bstart,
            benefit_end=bend,
            total_benefit=total,
            monthly_benefit=monthly,
            duration_months=months,
        ))
        if bend > phase1_end:
            phase1_end = bend

    phase1_total = sum(iv.total_benefit for iv in phase1_ivs)
    blocked = mwis_ids | _lifetime_excluded(all_mwis_policies, mwis_ids)
    future = [
        p for p in all_mwis_policies
        if p.id not in blocked and not p.is_supplementary
    ]

    future_ivs = _make_intervals(future, phase1_end, income_level, horizon)
    phase2_path = _dag_dp(future_ivs, phase1_end, gap_days)
    phase2_total = sum(iv.total_benefit for iv in phase2_path)

    phases: list[RoadmapPhase] = []
    if phase1_ivs:
        phases.append(RoadmapPhase(
            label="현재 최적 조합 (MWIS)",
            phase_start=user_start,
            phase_end=phase1_end,
            total_benefit=phase1_total,
            policies=phase1_ivs,
        ))
    if phase2_path:
        p2_end = max(iv.benefit_end for iv in phase2_path)
        phases.append(RoadmapPhase(
            label="환승 로드맵 (DAG DP)",
            phase_start=phase1_end + timedelta(days=gap_days),
            phase_end=p2_end,
            total_benefit=phase2_total,
            policies=phase2_path,
        ))

    transitions: list[tuple[str, str]] = []
    if phase1_ivs and phase2_path:
        last_p1 = max(phase1_ivs, key=lambda x: x.benefit_end)
        transitions.append((last_p1.title, phase2_path[0].title))
    for i in range(len(phase2_path) - 1):
        transitions.append((phase2_path[i].title, phase2_path[i + 1].title))

    all_ivs = [iv for ph in phases for iv in ph.policies]
    return FullRoadmap(
        phases=phases,
        total_benefit=phase1_total + phase2_total,
        total_months=sum(iv.duration_months for iv in all_ivs),
        transitions=transitions,
    )