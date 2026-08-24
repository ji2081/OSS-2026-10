from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

__all__ = ["TierLike", "resolve_tier"]


@runtime_checkable
class TierLike(Protocol):
    max_income_ratio: float | None
    monthly_benefit: int | None
    duration_months: int | None


def resolve_tier(tiers: list[TierLike], income_level: Optional[float]) -> TierLike | None:
    """소득 구간(income_level)에 맞는 policy tier를 결정한다.

    이전에는 graph_builder.py / roadmap_planner.py / policy_router.py 세 곳에
    동일한 로직이 복붙되어 있었고, income_level이 None일 때는 정렬 없이
    tiers[0]을 그대로 반환해 DB가 돌려주는 순서에 따라 결과가 달라질 수 있었다
    (관계에 order_by가 없어 순서가 보장되지 않음). 이제는 항상 먼저 정렬하므로
    income_level 유무와 무관하게 항상 같은 tier가 결정적으로 나온다.
    """
    if not tiers:
        return None

    sorted_tiers = sorted(
        tiers,
        key=lambda t: t.max_income_ratio if t.max_income_ratio is not None else 999,
    )

    if income_level is None:
        return sorted_tiers[0]

    return next(
        (t for t in sorted_tiers if t.max_income_ratio is None or t.max_income_ratio >= income_level),
        sorted_tiers[0],
    )
