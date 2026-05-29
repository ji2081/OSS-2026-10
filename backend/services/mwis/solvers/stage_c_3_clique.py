"""
stage_c_3_clique.py
===================

Stage C-③: 여그래프 변환 기반 최대 가중치 클릭(Maximum Weight Clique) MWIS 풀이기.

────────────────────────────────────────────────────────────────────────────────
[수학] MWIS ↔ MWC 동치 증명 (Complementary Graph Duality)
────────────────────────────────────────────────────────────────────────────────

원래 그래프 G = (V, E), 여그래프 Ḡ = (V, Ē) 에서 Ē = {(u,v) | (u,v) ∉ E, u≠v}.

정리: S ⊆ V 가 G 에서 독립 집합(Independent Set)  ⟺  S 가 Ḡ 에서 클릭(Clique)

증명:
    (→) S 가 G 의 독립 집합 → S 내 임의 두 노드 u,v 에 대해 (u,v) ∉ E
        → (u,v) ∈ Ē (여그래프 정의) → S 내 모든 쌍이 Ē 에 연결 → S 는 Ḡ 의 클릭. □
    (←) S 가 Ḡ 의 클릭 → S 내 임의 두 노드 u,v 에 대해 (u,v) ∈ Ē
        → (u,v) ∉ E (여그래프 정의) → S 내 어떤 쌍도 E 로 연결 안 됨 → S 는 G 의 독립 집합. □

따라서:
    MWIS(G) = MWC(Ḡ)     (최적값과 최적 집합 모두 동일)

────────────────────────────────────────────────────────────────────────────────
[성능 분석] 어떤 데이터셋에서 여그래프 변환이 유리한가?
────────────────────────────────────────────────────────────────────────────────

Case A — 원래 그래프 G 가 *밀집(Dense)* 할 때  [여그래프 변환 유리]
    상황: 청년 정책들 사이에 배타 조건이 많은 경우.
    G 가 밀집 → |E| → n(n-1)/2  →  Ḡ 가 *희소(Sparse)*
    - MWC 탐색 시 v 를 클릭에 추가하면 new_candidates = P ∩ N_Ḡ(v)
    - Ḡ 가 희소할수록 |N_Ḡ(v)| 가 작아 → new_candidates 가 빠르게 축소
    - 탐색 트리의 폭(Branching Factor)이 좁아지며 재귀 깊이가 얕아짐
    - 채색 상한선도 소수의 색으로 충분 → 타이트한 UB → 공격적 가지치기

Case B — 원래 그래프 G 가 *희소(Sparse)* 할 때  [원래 MWIS 방식 유리]
    상황: 청년 정책들 사이에 배타 조건이 거의 없는 경우.
    G 가 희소 → Ḡ 가 밀집 → MWC 탐색 시 new_candidates 가 크게 줄지 않음
    → 탐색 트리가 넓고 깊어져 오히려 BnB(Stage C-①)보다 느려질 수 있음.

결론:
    실제 서비스에서 배타 조건 밀도(|E| / n(n-1)/2)를 측정하여
    임계값(예: 0.5) 이상이면 ComplementGraphCliqueSolver 를,
    미만이면 BranchAndBoundSolver 를 동적으로 선택하는 전략이 이상적이다.

────────────────────────────────────────────────────────────────────────────────
[수학] 가중 채색 상한선 (Weighted Greedy Coloring Upper Bound for MWC)
────────────────────────────────────────────────────────────────────────────────

그래프 Ḡ[P] (후보 집합 P 에 대한 유도 부분 그래프)를 그리디로 채색할 때:
- 인접한 두 노드 (Ḡ 에서 연결) → 서로 다른 색 클래스
- 같은 색 클래스의 노드들 → Ḡ 에서 서로 비인접 → G 에서 서로 인접 (클릭 in G)

클릭(Ḡ 관점)은 모든 노드가 서로 Ḡ-인접이어야 하므로, 각 색 클래스에서
최대 1개의 노드만 클릭에 포함될 수 있다. 따라서::

    MWC(Ḡ[P]) ≤ Σ max{ w(v) | v ∈ color_class_k }  for k = 1..K

여기서 K = 사용된 색의 수(채색수).

밀집 Ḡ 에서는 K 가 작아져(= 색 클래스가 적어져) 상한선이 타이트해진다.
이것이 밀집 여그래프에서 채색 UB 가 특히 강력하게 동작하는 이유다.

참고:
- Tomita, E. & Seki, T. (2003), "An efficient branch-and-bound algorithm
  for finding a maximum clique." DMTCS.
- Niskanen, S. & Östergård, P. (2003), "Cliquer User's Guide."
────────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import time
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult

__all__ = ["ComplementGraphCliqueSolver"]


# ---------------------------------------------------------------------------
# 여그래프(Complement Graph) 구축
# ---------------------------------------------------------------------------
def _build_complement_adjacency(
    nodes: list[UUID],
    g_adj: dict[UUID, set[UUID]],
) -> dict[UUID, frozenset[UUID]]:
    """원래 그래프 G 의 인접 리스트로부터 여그래프 Ḡ 의 인접 리스트를 구축한다.

    N_Ḡ(v) = V \\ ({v} ∪ N_G(v))

    메모리 효율 설계
    ----------------
    - 각 노드의 Ḡ-이웃 집합을 ``frozenset`` 으로 저장한다.
      ``frozenset`` 은 불변이므로 알고리즘 도중 실수로 변경될 위험이 없고,
      해시 캐싱 덕분에 집합 포함 여부 검사(``u in comp_adj[v]``)가 O(1) 이다.
    - O(n²) 저장은 불가피하나, G 가 밀집할수록 |N_Ḡ(v)| 가 작아져
      이 변환이 적합한 케이스에서는 오히려 총 저장량이 절감된다.
    - 원본 ``g_adj`` 는 복사하지 않고 읽기 전용으로 참조한다.

    Parameters
    ----------
    nodes:
        그래프에 포함할 노드 목록.
    g_adj:
        원래 그래프 G 의 인접 리스트. build_graph() 의 반환값을 전달한다.

    Returns
    -------
    dict[UUID, frozenset[UUID]]
        Ḡ 의 인접 리스트. ``comp_adj[v]`` = v 와 Ḡ 에서 연결된 노드 집합.
    """
    node_set: frozenset[UUID] = frozenset(nodes)
    return {
        v: node_set - {v} - g_adj.get(v, frozenset())
        for v in nodes
    }


# ---------------------------------------------------------------------------
# 가중 채색 상한선 (Weighted Greedy Coloring Upper Bound)
# ---------------------------------------------------------------------------
def _weighted_coloring_ub(
    candidates: list[UUID],
    comp_adj: dict[UUID, frozenset[UUID]],
    weights: dict[UUID, int],
) -> int:
    """여그래프 Ḡ[candidates] 에 대한 그리디 가중 채색 상한선을 계산한다.

    알고리즘
    --------
    1. candidates 를 순서대로 순회하며 그리디 채색 수행.
    2. 각 노드 v 에 대해, Ḡ 에서 이미 채색된 v 의 이웃들이 사용 중인
       색 번호를 ``forbidden`` 집합으로 수집.
    3. forbidden 에 속하지 않는 최솟값 색 번호를 v 에 할당.
    4. 각 색 클래스마다 지금까지 할당된 노드 중 최대 가중치를 추적.
    5. 모든 색 클래스의 최대 가중치 합 = 상한선 반환.

    수학적 건전성(Soundness)
    -----------------------
    MWC(Ḡ[candidates]) ≤ Σ_k max_weight(color_class_k)  (모듈 상단 증명 참조)

    Parameters
    ----------
    candidates:
        현재 분기에서 클릭 확장 가능한 후보 노드 목록.
    comp_adj:
        Ḡ 의 인접 리스트 (``_build_complement_adjacency`` 의 반환값).
    weights:
        전체 노드의 가중치 딕셔너리.

    Returns
    -------
    int
        candidates 로만 이룰 수 있는 최대 클릭 가중치의 수학적 상한.

    시간 복잡도
    -----------
    O(|P| · d̄) — d̄ = candidates 내 평균 Ḡ-차수(degree in Ḡ[P]).
    Ḡ 가 희소할수록(G 가 밀집) d̄ 가 작아져 빠르게 계산된다.
    """
    if not candidates:
        return 0

    node_color: dict[UUID, int] = {}
    # 색 클래스 번호 → 해당 클래스에서 현재까지의 최대 가중치
    color_max_weight: list[int] = []

    for v in candidates:
        # Ḡ 에서 v 와 인접하고 이미 채색된 노드들의 색 집합 = forbidden
        forbidden: set[int] = {
            node_color[u]
            for u in comp_adj[v]
            if u in node_color
        }

        # 가장 작은 사용 가능한 색 번호 탐색
        color = 0
        while color in forbidden:
            color += 1

        node_color[v] = color

        # 색 클래스 테이블 갱신
        if color < len(color_max_weight):
            if weights[v] > color_max_weight[color]:
                color_max_weight[color] = weights[v]
        else:
            # 새 색 클래스 진입: 색 번호가 연속이 아닐 경우를 대비해 0으로 패딩
            while len(color_max_weight) < color:
                color_max_weight.append(0)
            color_max_weight.append(weights[v])

    return sum(color_max_weight)


# ---------------------------------------------------------------------------
# 최대 가중치 클릭 Branch & Bound 탐색
# ---------------------------------------------------------------------------
def _mwc_branch_and_bound(
    candidates: list[UUID],
    current_clique: list[UUID],
    current_weight: int,
    comp_adj: dict[UUID, frozenset[UUID]],
    weights: dict[UUID, int],
    best: list[int | list[UUID]],  # [best_weight, best_clique]
    rec_count: list[int],
) -> None:
    """여그래프 Ḡ 위에서 최대 가중치 클릭(MWC)을 분기한정법으로 탐색한다.

    탐색 전략
    ---------
    **호출 진입 시 — 전역 가지치기(Call-level Pruning)**:
        ``current_weight + 채색_UB(candidates) ≤ best_weight`` 이면
        이 서브트리 전체를 즉시 포기한다. 밀집 Ḡ 에서 채색수(K)가 작으므로
        UB 가 타이트하게 계산되어 공격적 가지치기가 가능하다.

    **분기 내부 — 접미사 합 가지치기(Suffix-sum Pruning)**:
        candidates 가 가중치 내림차순으로 정렬되어 있으므로, 현재 위치 i
        이후의 가중치 합 suffix[i] 이 최상의 경우(모두 선택)에 해당한다.
        ``current_weight + suffix[i] ≤ best_weight`` 이면 i 이후의 모든
        분기를 한번에 건너뛸 수 있다. O(1) 검사로 O(n) 재귀를 절약한다.

    **분기 실행 — 클릭 확장**:
        v 를 클릭에 추가할 때 new_candidates = P ∩ N_Ḡ(v) 를 계산한다.
        즉, v 와 Ḡ 에서 인접한(= G 에서 비인접한) 후보만 남긴다.
        후보 순서(가중치 내림차순)를 유지하며 필터링하므로 하위 레벨에서도
        동일한 순서 보장이 유지된다.

    Parameters
    ----------
    candidates:
        현재 클릭을 확장할 수 있는 후보 노드 목록. 가중치 내림차순 정렬 전제.
    current_clique:
        현재까지 선택된 노드 목록. 역추적(Backtrack) 시 pop 된다.
    current_weight:
        ``current_clique`` 의 가중치 합.
    comp_adj:
        Ḡ 의 전역 인접 리스트.
    weights:
        전체 노드의 가중치 딕셔너리.
    best:
        ``[best_weight, best_clique]`` — 가변 레퍼런스로 최고 기록을 공유.
    rec_count:
        ``[count]`` — 재귀 호출 횟수 누적 카운터.
    """
    rec_count[0] += 1

    # ── 호출 레벨 가지치기: 채색 UB ─────────────────────────────────────────
    ub = current_weight + _weighted_coloring_ub(candidates, comp_adj, weights)
    if ub <= best[0]:
        return  # ★ 이 서브트리는 어떻게 탐색해도 최고 기록을 경신 불가 → 포기

    # ── 단말 노드: 클릭 확정 ────────────────────────────────────────────────
    if not candidates:
        if current_weight > best[0]:
            best[0] = current_weight
            best[1] = list(current_clique)
        return

    # ── 분기 내부 빠른 가지치기를 위한 접미사 합 사전 계산 ──────────────────
    # candidates 는 가중치 내림차순 → suffix[i] = candidates[i:] 의 가중치 합
    # 이는 'i 번째 이후 노드를 모조리 클릭에 넣는' 이상적 시나리오의 상한값.
    n = len(candidates)
    suffix: list[int] = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + weights[candidates[i]]

    # ── 분기 탐색 ────────────────────────────────────────────────────────────
    for i, v in enumerate(candidates):
        # 접미사 합 가지치기: 이 위치 이후 모든 노드를 더해도 최고 기록 미달 → 조기 종료
        if current_weight + suffix[i] <= best[0]:
            break  # candidates 가 내림차순이므로 이후 i' > i 도 동일 조건 → break

        # Ḡ 에서 v 와 인접한(= G 에서 비인접한) 노드만 new_candidates 로 선별.
        # candidates[i+1:] 에서 comp_adj[v] 와 교집합을 취한다.
        # 슬라이싱으로 이전에 분기한 노드들은 자동 제외(중복 탐색 방지).
        comp_neighbors_v: frozenset[UUID] = comp_adj[v]
        new_candidates: list[UUID] = [
            u for u in candidates[i + 1:]
            if u in comp_neighbors_v
        ]

        # ── 분기 ①: v 를 클릭에 포함 ────────────────────────────────────────
        current_clique.append(v)
        _mwc_branch_and_bound(
            new_candidates,
            current_clique,
            current_weight + weights[v],
            comp_adj,
            weights,
            best,
            rec_count,
        )
        current_clique.pop()  # 역추적(Backtrack): 클릭에서 v 제거

        # 분기 ②: v 를 클릭에서 제외 → 루프의 다음 반복(i+1 번째 노드 탐색)


# ---------------------------------------------------------------------------
# 공개 풀이 클래스
# ---------------------------------------------------------------------------
class ComplementGraphCliqueSolver(BaseMWISSolver):
    """여그래프 변환 후 최대 가중치 클릭(MWC) 탐색으로 MWIS 정확해를 구한다.

    작동 원리
    ---------
    1. 원래 그래프 G 의 인접 리스트를 여그래프 Ḡ 로 변환한다.
       (두 노드가 G 에서 *비인접* ↔ Ḡ 에서 *인접*)
    2. Ḡ 위에서 가중 채색 UB + 접미사 합 UB 를 결합한 분기한정법으로
       최대 가중치 클릭을 찾는다.
    3. MWC(Ḡ) 의 해는 곧 MWIS(G) 의 해와 동일하다.

    적합한 사용 시나리오
    --------------------
    G 의 간선 밀도 ρ = |E| / (n(n-1)/2) 가 높을수록(≳ 0.5) 이 풀이기가
    BranchAndBoundSolver(Stage C-①)보다 빠른 경향이 있다.
    낮은 밀도에서는 BranchAndBoundSolver 가 더 유리하다.
    (모듈 상단 '성능 분석' 섹션 참조)
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        """여그래프 기반 MWC 탐색으로 MWIS 를 해결한다.

        Parameters
        ----------
        adjacency_list:
            ``{정책_id: {배타_정책_id, ...}}`` 무방향 인접 리스트.
        weights:
            ``{정책_id: total_benefit}`` 가중치 딕셔너리.

        Returns
        -------
        SolverResult
            선택된 정책 ID 목록, 총 수혜 금액, 실행 시간(ms), 재귀 호출 횟수.
        """
        start_ns = time.perf_counter_ns()

        # 가중치가 0 이하인 노드는 최적해에 기여하지 않으므로 사전 제거.
        active_nodes: list[UUID] = [n for n in weights if weights[n] > 0]

        if not active_nodes:
            return SolverResult(
                selected_ids=[],
                total_benefit=0,
                execution_time_ms=_ns_to_ms(time.perf_counter_ns() - start_ns),
                recursion_count=0,
            )

        # ── 1단계: 여그래프 Ḡ 구축 ───────────────────────────────────────────
        comp_adj: dict[UUID, frozenset[UUID]] = _build_complement_adjacency(
            active_nodes, adjacency_list
        )

        # ── 2단계: 초기 정렬 (Heuristic Ordering) ───────────────────────────
        # 가중치 내림차순 정렬: 탐색 초반에 무거운 노드를 먼저 클릭에 포함시켜
        # 빠르게 높은 하한(Best Value)을 확보 → 이후 가지치기 효율 극대화.
        sorted_nodes: list[UUID] = sorted(
            active_nodes,
            key=lambda n: weights[n],
            reverse=True,
        )

        # ── 3단계: MWC 분기한정 탐색 ────────────────────────────────────────
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


# ---------------------------------------------------------------------------
# 내부 유틸리티
# ---------------------------------------------------------------------------
def _ns_to_ms(nanoseconds: int) -> float:
    """나노초(ns) → 밀리초(ms) 변환. ``perf_counter_ns()`` 결과용."""
    return nanoseconds / 1_000_000
