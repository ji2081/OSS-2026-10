"""
stage_c_3_clique.py

Stage C-③: 여그래프(Complement Graph) 변환 기반 최대 가중치 클릭(MWC) MWIS 풀이기.

[수학] MWIS ↔ MWC 동치
----------------------
원래 그래프 G의 여그래프 Ḡ에서: S가 G의 독립 집합 ⟺ S가 Ḡ의 클릭.
따라서 MWIS(G) = MWC(Ḡ) (최적값·최적 집합 모두 동일).

[수학] 가중 채색 상한선
-----------------------
Ḡ[P]를 그리디로 채색하면, 같은 색 클래스의 노드들은 G에서 서로 인접(클릭 후보 아님)
→ 각 색 클래스에서 최대 1개만 클릭에 포함 가능.
    MWC(Ḡ[P]) <= Σ max(w(v) | v ∈ color_class_k)
밀집 Ḡ일수록 색 수(K)가 적어져 상한선이 타이트해진다.

언제 유리한가
-------------
배타 조건 밀도 ρ = |E| / (n(n-1)/2)가 높을수록(≳0.5) 이 방식이
BranchAndBoundSolver(Stage C-①)보다 빠른 경향이 있다. 밀도가 낮으면 반대.

참고: Tomita & Seki (2003); Niskanen & Östergård (2003), Cliquer User's Guide
"""

from __future__ import annotations

import time
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult

__all__ = ["ComplementGraphCliqueSolver"]


def _build_complement_adjacency(
    nodes: list[UUID],
    g_adj: dict[UUID, set[UUID]],
) -> dict[UUID, frozenset[UUID]]:
    """G의 인접 리스트로부터 여그래프 Ḡ의 인접 리스트를 구축한다.

    N_Ḡ(v) = V \\ ({v} ∪ N_G(v))
    """
    node_set = frozenset(nodes)
    return {v: node_set - {v} - g_adj.get(v, frozenset()) for v in nodes}


def _weighted_coloring_ub(
    candidates: list[UUID],
    comp_adj: dict[UUID, frozenset[UUID]],
    weights: dict[UUID, int],
) -> int:
    """Ḡ[candidates]에 대한 그리디 가중 채색 상한선을 계산한다.

    각 노드에 Ḡ-이웃이 쓰지 않은 가장 작은 색을 할당하고,
    색 클래스별 최대 가중치의 합을 반환한다.
    """
    if not candidates:
        return 0

    node_color: dict[UUID, int] = {}
    color_max_weight: list[int] = []

    for v in candidates:
        forbidden = {node_color[u] for u in comp_adj[v] if u in node_color}

        color = 0
        while color in forbidden:
            color += 1
        node_color[v] = color

        if color < len(color_max_weight):
            if weights[v] > color_max_weight[color]:
                color_max_weight[color] = weights[v]
        else:
            while len(color_max_weight) < color:
                color_max_weight.append(0)
            color_max_weight.append(weights[v])

    return sum(color_max_weight)


def _mwc_branch_and_bound(
    candidates: list[UUID],
    current_clique: list[UUID],
    current_weight: int,
    comp_adj: dict[UUID, frozenset[UUID]],
    weights: dict[UUID, int],
    best: list[int | list[UUID]],
    rec_count: list[int],
) -> None:
    """Ḡ 위에서 최대 가중치 클릭(MWC)을 분기한정법으로 탐색한다.

    - 진입 시 채색 상한선으로 가지치기.
    - candidates는 가중치 내림차순 정렬 상태 → 접미사 합으로 추가 가지치기.
    - v를 클릭에 추가하면 new_candidates = candidates ∩ N_Ḡ(v).
    """
    rec_count[0] += 1

    ub = current_weight + _weighted_coloring_ub(candidates, comp_adj, weights)
    if ub <= best[0]:
        return  # 채색 UB <= 최고 기록 → 가지치기

    if not candidates:
        if current_weight > best[0]:
            best[0] = current_weight
            best[1] = list(current_clique)
        return

    # 접미사 합: candidates[i:]를 전부 더해도 최고 기록 미달이면 조기 종료
    n = len(candidates)
    suffix: list[int] = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + weights[candidates[i]]

    for i, v in enumerate(candidates):
        if current_weight + suffix[i] <= best[0]:
            break  # 내림차순이므로 이후도 동일 → 전체 종료

        comp_neighbors_v = comp_adj[v]
        new_candidates = [u for u in candidates[i + 1:] if u in comp_neighbors_v]

        current_clique.append(v)
        _mwc_branch_and_bound(
            new_candidates, current_clique, current_weight + weights[v],
            comp_adj, weights, best, rec_count,
        )
        current_clique.pop()


class ComplementGraphCliqueSolver(BaseMWISSolver):
    """여그래프 변환 후 최대 가중치 클릭(MWC) 탐색으로 MWIS 정확해를 구한다.

    배타 조건 밀도가 높은 그래프에서 BranchAndBoundSolver보다 유리하다.
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        start_ns = time.perf_counter_ns()

        active_nodes = [n for n in weights if weights[n] > 0]
        if not active_nodes:
            return SolverResult(
                selected_ids=[],
                total_benefit=0,
                execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
                recursion_count=0,
            )

        comp_adj = _build_complement_adjacency(active_nodes, adjacency_list)

        # 가중치 내림차순 정렬 → 초반에 무거운 노드로 높은 하한 확보
        sorted_nodes = sorted(active_nodes, key=lambda n: weights[n], reverse=True)

        best: list[int | list[UUID]] = [0, []]
        rec_count: list[int] = [0]

        _mwc_branch_and_bound(
            candidates=sorted_nodes,
            current_clique=[],
            current_weight=0,
            comp_adj=comp_adj,
            weights=weights,
            best=best,
            rec_count=rec_count,
        )

        return SolverResult(
            selected_ids=best[1],           # type: ignore[arg-type]
            total_benefit=best[0],          # type: ignore[arg-type]
            execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
            recursion_count=rec_count[0],
        )


def _ns_to_ms(nanoseconds: int) -> float:
    """나노초를 밀리초로 변환한다."""
    return nanoseconds / 1_000_000