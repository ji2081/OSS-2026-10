"""
stage_c_1_bnb.py

Stage C-①: Branch and Bound(분기한정법) 기반 MWIS 정확해 풀이기.

핵심 아이디어
-------------
- 후보 노드를 '단위 이득(weight / (degree+1))' 내림차순으로 정렬해
  탐색 초반에 높은 하한값(best_value)을 빠르게 확보한다.
- 각 분기 진입 시 상한선(Upper Bound)을 계산해
  current_value + UB <= best_value 이면 해당 서브트리를 가지치기한다.

[수학] 매칭 기반 LP 완화 상한선
-----------------------------
MWIS의 LP 완화는 다음과 동일하다:
    Maximize Σ wᵢxᵢ  s.t.  xᵤ + x_v <= 1 (∀(u,v)∈E), 0<=xᵢ<=1

임의의 매칭 M ⊆ E 에 대해:
    OPT_MWIS <= Σ wᵥ (전체) - Σ min(wᵤ, w_v) ((u,v)∈M)

즉 min(wᵤ,w_v)가 큰 간선부터 그리디로 매칭할수록 상한이 타이트해진다.

참고: Nemhauser & Trotter (1975), Hochbaum (1982)
"""

from __future__ import annotations

import time
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult

__all__ = ["BranchAndBoundSolver"]


class BranchAndBoundSolver(BaseMWISSolver):
    """분기한정법 기반 MWIS 정확해 풀이기.

    최악 O(2^n)이지만, 정책 배타 그래프처럼 희소한 그래프에서는
    가지치기로 탐색 노드 수가 크게 줄어 실용적인 시간 내에 동작한다.
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        start_ns = time.perf_counter_ns()

        # 가중치 0 이하 노드는 최적해에 기여하지 않으므로 제외
        active_nodes = [n for n in weights if weights[n] > 0]
        if not active_nodes:
            return SolverResult(
                selected_ids=[],
                total_benefit=0,
                execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
                recursion_count=0,
            )

        # 단위 이득(weight / (degree+1)) 내림차순 정렬 → 초반에 높은 하한 확보
        sorted_candidates: list[UUID] = sorted(
            active_nodes,
            key=lambda n: weights[n] / (len(adjacency_list[n]) + 1),
            reverse=True,
        )

        best_value: list[int] = [0]
        best_ids: list[list[UUID]] = [[]]
        recursion_count: list[int] = [0]

        def _branch_and_bound(
            candidates: list[UUID],
            current_ids: list[UUID],
            current_value: int,
        ) -> None:
            recursion_count[0] += 1

            # 상한선 <= 현재 최고 기록이면 이 서브트리는 가지치기
            ub = current_value + _matching_upper_bound(candidates, adjacency_list, weights)
            if ub <= best_value[0]:
                return

            if not candidates:
                if current_value > best_value[0]:
                    best_value[0] = current_value
                    best_ids[0] = list(current_ids)
                return

            # 후보 맨 앞 노드 v를 '포함 vs 제외'로 분기
            v = candidates[0]
            rest = candidates[1:]

            # 포함: v의 이웃(배타 관계)을 후보에서 제거
            neighbors_of_v = adjacency_list[v]
            pruned_candidates = [u for u in rest if u not in neighbors_of_v]
            current_ids.append(v)
            _branch_and_bound(pruned_candidates, current_ids, current_value + weights[v])
            current_ids.pop()

            # 제외: v 없이 나머지 후보로 계속 탐색
            _branch_and_bound(rest, current_ids, current_value)

        _branch_and_bound(sorted_candidates, [], 0)

        return SolverResult(
            selected_ids=best_ids[0],
            total_benefit=best_value[0],
            execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
            recursion_count=recursion_count[0],
        )


def _matching_upper_bound(
    candidates: list[UUID],
    adjacency_list: dict[UUID, set[UUID]],
    weights: dict[UUID, int],
) -> int:
    """후보 집합에서 달성 가능한 MWIS 가중치의 상한선(매칭 기반 LP 완화).

    1. 후보 가중치 합을 베이스라인으로 둔다.
    2. 후보 부분 그래프의 간선을 min(wᵤ,w_v) 내림차순으로 정렬한다.
    3. 그리디로 최대 매칭을 구성하며, 매칭된 간선마다 min(wᵤ,w_v)를 차감한다.
    """
    if not candidates:
        return 0

    candidate_set = frozenset(candidates)
    total = sum(weights[v] for v in candidates)

    # 후보 부분 그래프의 간선 수집 (u < v로 중복 제거)
    edges: list[tuple[int, UUID, UUID]] = []
    for u in candidates:
        for v in adjacency_list[u]:
            if v in candidate_set and u < v:
                edges.append((min(weights[u], weights[v]), u, v))

    edges.sort(key=lambda e: e[0], reverse=True)

    matched: set[UUID] = set()
    for saving, u, v in edges:
        if u in matched or v in matched:
            continue
        matched.add(u)
        matched.add(v)
        total -= saving

    return total


def _ns_to_ms(nanoseconds: int) -> float:
    """나노초를 밀리초로 변환한다."""
    return nanoseconds / 1_000_000