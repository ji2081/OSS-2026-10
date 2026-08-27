"""수혜 기간·가중치 산정 회귀 테스트.

아래 두 결함이 재발하지 않도록 고정한다.
  1) _add_months 가 day를 1로 고정해 월 중순 시작 정책의 기간이 짧아지던 문제
  2) _overlap_months 가 모든 정책을 1개월씩 과소 산정하던 문제
     (12개월 정책 -> 11개월, 1개월 정책 -> 0개월로 가중치 소멸)
"""

import datetime

import pytest

from services.mwis.graph_builder import (
    HORIZON_MONTHS,
    _add_months,
    _overlap_months,
    _periods_overlap,
    current_window,
)

D = datetime.date
WINDOW_START = D(2026, 1, 1)
WINDOW_END = D(2026, 12, 31)


def _period(start: D, duration: int, lag: int = 0):
    s = start + datetime.timedelta(days=lag)
    return s, _add_months(s, duration) - datetime.timedelta(days=1)


def _months(start: D, duration: int, lag: int = 0) -> int:
    return _overlap_months(_period(start, duration, lag), WINDOW_START, WINDOW_END)


@pytest.mark.parametrize(
    "start, duration, expected",
    [
        (D(2026, 1, 1), 12, 12),   # 이전 구현: 11
        (D(2026, 1, 1), 6, 6),     # 이전 구현: 5
        (D(2026, 6, 1), 3, 3),     # 이전 구현: 2
        (D(2026, 11, 1), 1, 1),    # 이전 구현: 0 (가중치 소멸)
        (D(2026, 12, 1), 1, 1),    # 이전 구현: 0
    ],
)
def test_overlap_months_counts_full_duration(start, duration, expected):
    assert _months(start, duration) == expected


def test_window_clips_overflowing_period():
    # 10월 시작 12개월 -> window 안에서는 3개월만 인정
    assert _months(D(2026, 10, 1), 12) == 3


def test_add_months_preserves_day():
    assert _add_months(D(2026, 3, 15), 12) == D(2027, 3, 15)


def test_add_months_clamps_to_month_end():
    assert _add_months(D(2026, 1, 31), 1) == D(2026, 2, 28)


def test_mid_month_period_is_exactly_duration():
    start = D(2026, 3, 15)
    period = _period(start, 12)
    assert period[1] == D(2027, 3, 14)
    assert _overlap_months(period, start, period[1]) == 12


def test_lag_days_shift_start():
    period = _period(D(2026, 1, 1), 3, lag=30)
    assert period[0] == D(2026, 1, 31)


def test_current_window_is_exactly_horizon_months():
    start, end = current_window(D(2026, 8, 26))
    assert end == D(2027, 8, 25)
    assert _overlap_months((start, end), start, end) == HORIZON_MONTHS


def test_sequential_policies_do_not_overlap():
    # 환승: 앞 정책 종료 다음 날 시작하면 배타 간선을 만들지 않는다
    a = _period(D(2026, 1, 1), 6)
    b = _period(D(2026, 7, 1), 6)
    assert _periods_overlap(a, b) is False


def test_concurrent_policies_overlap():
    a = _period(D(2026, 1, 1), 6)
    b = _period(D(2026, 4, 1), 6)
    assert _periods_overlap(a, b) is True


def test_weight_reflects_full_period():
    monthly = 500_000
    assert monthly * _months(D(2026, 1, 1), 12) == 6_000_000
