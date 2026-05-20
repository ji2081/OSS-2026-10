"""
stage_c_1_bnb.py
================

Stage C-①: Branch and Bound (분기한정법) MWIS 구현체.

알고리즘 개요
-------------
단순 DFS 백트래킹이 '정답을 찾기 위해 모든 경우의 수를 탐색'하는 것과 달리,
분기한정법은 탐색 도중 "이 방향의 탐색을 아무리 잘해도 현재 최고 기록을
넘을 수 없다"는 수학적 증명(Upper Bound)이 나오면 해당 서브트리 전체를
가지치기(Prune)하여 탐색 공간을 극적으로 축소한다.

핵심 구성 3요소
---------------
1. **탐색 노드 정렬 (Heuristic Ordering)**
   탐색 전, 후보 노드들을 '단위 이득(weight / (degree + 1))'이 높은 순으로
   정렬한다. 이렇게 하면 초반 탐색에서 "질 좋은" 노드들을 먼저 선택하게 되어
   빠르게 높은 하한값(Lower Bound, 최고 기록)을 확보한다. 최고 기록이 높을수록
   이후 Upper Bound 기반 가지치기가 공격적으로 동작하여 전체 탐색 시간이 단축된다.

2. **상한선 계산 (Matching-based LP Relaxation Upper Bound)**
   현재 선택 가능한 후보 집합(candidates)에서 얻을 수 있는 이론적 최대치를
   정교하게 계산한다. 이 구현에서는 **최대 가중치 매칭(Greedy Matching)** 기반
   LP 완화(Relaxation) 기법을 사용한다. (수학적 증명은 아래 섹션 참조)

3. **가지치기 (Pruning)**
   current_value + upper_bound(candidates) ≤ best_value 이면
   해당 서브트리 전체를 즉시 포기하고 역추적(Backtrack)한다.

────────────────────────────────────────────────────────────────────────────
[수학] 매칭 기반 LP 완화 상한선 (Matching-based LP Relaxation Upper Bound)
────────────────────────────────────────────────────────────────────────────

MWIS의 LP 완화(Fractional Relaxation)는 다음 선형 계획법과 동일하다::

    Maximize:   Σᵢ wᵢ · xᵢ
    subject to: xᵤ + x_v ≤ 1    (∀ 간선 (u,v) ∈ E)
                0 ≤ xᵢ ≤ 1

이 LP의 최적값 OPT_LP 는 항상 OPT_MWIS ≤ OPT_LP 를 만족한다.
(정수 완화이므로 실수 해가 반드시 정수 해보다 크거나 같다)

임의의 매칭(Matching) M ⊆ E 에 대해 다음 듀얼 실현 가능 상한을 유도할 수 있다::

    OPT_MWIS ≤ OPT_LP
             ≤ Σ wᵥ (v ∉ V(M))  +  Σ max(wᵤ, w_v) ((u,v) ∈ M)
             =  Σ wᵥ (전체)  −  Σ min(wᵤ, w_v) ((u,v) ∈ M)

증명 스케치:
- 매칭 M 내의 간선 (u, v) 각각에 대해 xᵤ + x_v ≤ 1 이므로
  wᵤ·xᵤ + w_v·x_v ≤ max(wᵤ, w_v) · (xᵤ + x_v) ≤ max(wᵤ, w_v)
- 따라서 전체 목적함수 ≤ Σ_{V\\V(M)} wᵥ + Σ_{M} max(wᵤ, w_v)
- 이를 변형하면: = Σ_V wᵥ - Σ_M min(wᵤ, w_v)

매칭이 클수록(절약량 Σ min()이 클수록) 상한이 타이트해지므로,
그리디로 min(wᵤ, w_v)가 큰 간선부터 매칭하여 가장 타이트한 상한을 구한다.

참고 문헌:
- Nemhauser & Trotter (1975), "Vertex packings: structural properties and algorithms"
- Hochbaum (1982), "Approximation algorithms for the set covering and vertex cover problems"
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import time
from uuid import UUID

from backend.services.mwis.base_solver import BaseMWISSolver, SolverResult

__all__ = ["BranchAndBoundSolver"]


class BranchAndBoundSolver(BaseMWISSolver):
    """분기한정법(Branch and Bound) 기반 MWIS 정확해(Exact) 풀이기.

    시간 복잡도
    -----------
    - 최악: O(2ⁿ)  — 가지치기가 전혀 작동하지 않는 완전 그래프
    - 실용적: 밀집 배타 그래프에서 DFS 백트래킹 대비 탐색 노드 수를
      수십~수백 배 줄이는 것이 실험적으로 확인된다.

    정책 추천 도메인 특성상 배타 조건 그래프는 희소(sparse)하고,
    정책 수도 일반적으로 수십~수백 개 수준이므로 정확해를 현실적인
    시간 내에 구하는 데 적합한 알고리즘이다.
    """

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        """분기한정법으로 MWIS 정확해를 구한다.

        Parameters
        ----------
        adjacency_list:
            ``{정책_id: {배타_정책_id, ...}}`` 무방향 인접 리스트.
            ``graph_builder.build_graph()`` 의 반환값을 그대로 전달한다.
        weights:
            ``{정책_id: total_benefit}`` 가중치 딕셔너리.

        Returns
        -------
        SolverResult
            선택된 정책 ID, 총 수혜 금액, 실행 시간(ms), 재귀 호출 횟수.
        """
        start_ns = time.perf_counter_ns()

        # 가중치 0 또는 음수 노드는 최적해에 기여할 수 없으므로 사전 제거.
        # (Total_benefit 이 None → 0 으로 정규화된 상태임을 전제)
        active_nodes = [n for n in weights if weights[n] > 0]

        # 빈 그래프 조기 반환 — 재귀 호출 불필요.
        if not active_nodes:
            return SolverResult(
                selected_ids=[],
                total_benefit=0,
                execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
                recursion_count=0,
            )

        # ── 1단계: 탐색 노드 정렬 (Heuristic) ─────────────────────────
        # '단위 이득' = weight / (degree + 1)  이 높은 노드를 앞에 배치.
        # 초반 탐색에서 좋은 노드를 선택 → 낮은 depth 에서 높은 LB 확보
        # → 이후 UB 기반 가지치기 효율 극대화.
        sorted_candidates: list[UUID] = sorted(
            active_nodes,
            key=lambda n: weights[n] / (len(adjacency_list[n]) + 1),
            reverse=True,
        )

        # ── 2단계: 분기한정 DFS ─────────────────────────────────────────
        # 가변 레퍼런스를 리스트로 감싸 클로저 내에서 갱신 가능하도록 함.
        # Python 3.10 에서는 nonlocal 대신 이 패턴이 성능상 미세하게 유리.
        best_value: list[int] = [0]
        best_ids: list[list[UUID]] = [[]]
        recursion_count: list[int] = [0]

        def _branch_and_bound(
            candidates: list[UUID],  # 현재 선택 가능한 후보 노드들 (정렬 순서 유지)
            current_ids: list[UUID],  # 현재까지 선택된 노드들
            current_value: int,       # 현재까지 누적된 수혜 금액
        ) -> None:
            """재귀적 분기한정 탐색 내부 함수.

            Parameters
            ----------
            candidates:
                현재 분기에서 선택 가능한 후보 노드 목록. 부모 노드를
                '포함'하는 분기에서는 부모의 이웃이 모두 제거된 상태다.
            current_ids:
                현재 경로에서 선택된 노드 누적 목록. 역추적 시 pop 된다.
            current_value:
                ``current_ids`` 에 해당하는 가중치 합산.
            """
            recursion_count[0] += 1

            # ── 가지치기 판정 ─────────────────────────────────────────
            # Upper Bound: 지금 상태에서 남은 후보를 아무리 최적으로 골라도
            # 달성할 수 없는 이론적 최대치. 이 값이 현재 최고 기록 이하이면
            # 이 서브트리에서 더 좋은 해가 나올 가능성이 0 이므로 즉시 포기.
            ub = current_value + _matching_upper_bound(
                candidates, adjacency_list, weights
            )
            if ub <= best_value[0]:
                return  # ★ 가지치기(Prune)

            # ── 단말 노드 처리 ────────────────────────────────────────
            if not candidates:
                # 후보가 없음 = 이 분기의 최종 해 확정.
                if current_value > best_value[0]:
                    best_value[0] = current_value
                    best_ids[0] = list(current_ids)  # 현재 경로 스냅샷
                return

            # ── 분기 (Branch) ─────────────────────────────────────────
            # 탐색 변수: 후보 목록 맨 앞 노드 v 를 '포함 vs 제외'로 분기.
            v = candidates[0]
            rest = candidates[1:]

            # ── 분기 ①: v 를 독립 집합에 포함 ─────────────────────────
            # v 의 이웃은 모두 배타 관계이므로 후보에서 제거.
            # 정렬 순서를 유지하면서 이웃을 O(n) 에 필터링한다.
            neighbors_of_v: set[UUID] = adjacency_list[v]
            pruned_candidates = [u for u in rest if u not in neighbors_of_v]

            current_ids.append(v)
            _branch_and_bound(pruned_candidates, current_ids, current_value + weights[v])
            current_ids.pop()  # 역추적(Backtrack)

            # ── 분기 ②: v 를 독립 집합에서 제외 ──────────────────────
            # v 를 선택하지 않고 나머지 후보만으로 탐색 계속.
            _branch_and_bound(rest, current_ids, current_value)

        # DFS 시작 — 초기 상태: 선택된 노드 없음, 누적 금액 0
        _branch_and_bound(sorted_candidates, [], 0)

        return SolverResult(
            selected_ids=best_ids[0],
            total_benefit=best_value[0],
            execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
            recursion_count=recursion_count[0],
        )


# ---------------------------------------------------------------------------
# 상한선 계산 (모듈-레벨 순수 함수 — 테스트 및 재사용 용이)
# ---------------------------------------------------------------------------
def _matching_upper_bound(
    candidates: list[UUID],
    adjacency_list: dict[UUID, set[UUID]],
    weights: dict[UUID, int],
) -> int:
    """매칭 기반 LP 완화 상한선을 계산한다.

    이 함수가 반환하는 값은 항상 실제 MWIS 최적값 이상임이 수학적으로
    보장된다. (모듈 상단 '수학' 섹션의 증명 참조)

    알고리즘
    --------
    1. 후보 노드들의 가중치 합을 베이스라인으로 설정 (``total``).
    2. 후보 부분 그래프의 충돌 간선들을 ``min(wᵤ, w_v)`` 내림차순 정렬.
       (절약량이 큰 간선부터 매칭해야 타이트한 상한을 얻을 수 있다)
    3. 그리디 최대 매칭: 아직 매칭되지 않은 간선 (u, v) 를 순서대로 선택,
       두 끝점 중 가중치가 낮은 쪽의 값만큼 ``total`` 에서 차감한다.
       이미 매칭된 노드가 포함된 간선은 건너뛴다.
    4. 최종 ``total`` = 타이트한 상한선 반환.

    Parameters
    ----------
    candidates:
        현재 분기에서 선택 가능한 후보 노드 순서 리스트.
    adjacency_list:
        전체 그래프의 무방향 인접 리스트.
    weights:
        전체 그래프의 가중치 딕셔너리.

    Returns
    -------
    int
        후보 집합에서 달성 가능한 MWIS 가중치의 수학적 상한.
        OPT_MWIS(candidates) ≤ 반환값이 항상 성립.

    시간 복잡도
    -----------
    O(E' log E') — E' 는 후보 부분 그래프의 간선 수.
    최악의 경우 O(n² log n) 이지만, 실제 배타 조건 그래프는 희소하므로
    실용적 성능은 이보다 훨씬 빠르다.
    """
    if not candidates:
        return 0

    candidate_set: frozenset[UUID] = frozenset(candidates)
    total: int = sum(weights[v] for v in candidates)

    # 후보 부분 그래프의 간선을 수집.
    # UUID 의 대소 비교(u < v)로 중복 간선(u,v 와 v,u)을 제거한다.
    edges: list[tuple[int, UUID, UUID]] = []
    for u in candidates:
        for v in adjacency_list[u]:
            if v in candidate_set and u < v:
                edges.append((min(weights[u], weights[v]), u, v))

    # 절약량(min weight)이 큰 간선부터 처리 → 타이트한 상한 확보
    edges.sort(key=lambda e: e[0], reverse=True)

    matched: set[UUID] = set()
    for saving, u, v in edges:
        if u in matched or v in matched:
            continue  # 이미 매칭된 끝점 → 이 간선은 독립 매칭에 사용 불가
        matched.add(u)
        matched.add(v)
        total -= saving  # 이 간선이 있으면 최소 saving 만큼은 얻지 못한다

    return total


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------
def _ns_to_ms(nanoseconds: int) -> float:
    """나노초(ns)를 밀리초(ms)로 변환한다.

    ``time.perf_counter_ns()`` 는 ``perf_counter()`` 보다 부동소수점 오차가
    없는 정수 반환이므로 고정밀 벤치마크에 더 적합하다.
    """
    return nanoseconds / 1_000_000
