# backend/services/mwis/solvers/stage_c_preprocess.py

import time
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult


class PreprocessSolver(BaseMWISSolver):
    """
    Stage C: 그래프 전처리 + DFS 백트래킹
    
    핵심 아이디어:
    - 고립 노드(배타 관계 없음) → 무조건 선택, 탐색에서 제외
    - 배타 관계 있는 노드만 DFS 탐색
    
    시간복잡도: O(2^K), K = 배타 관계 있는 노드 수 (K << N)
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        start = time.perf_counter()
        recursion_count = 0

        # 1단계: 고립 노드 / 연결 노드 분리
        isolated = []
        connected = []
        for node_id, neighbors in adjacency_list.items():
            if neighbors:
                connected.append(node_id)
            else:
                isolated.append(node_id)

        # 고립 노드는 무조건 전부 선택
        isolated_benefit = sum(weights[n] for n in isolated)

        # 2단계: 연결 노드만 DFS
        nodes = connected
        n = len(nodes)
        idx_map = {node_id: i for i, node_id in enumerate(nodes)}

        conflict_map: list[set] = []
        for node_id in nodes:
            conflicts = {idx_map[nb] for nb in adjacency_list[node_id] if nb in idx_map}
            conflict_map.append(conflicts)

        best = {"value": 0, "subset": []}
        memo: dict = {}

        def dfs(idx: int, selected: list[int], current_value: int, excluded: set):
            nonlocal recursion_count
            recursion_count += 1

            if current_value > best["value"]:
                best["value"] = current_value
                best["subset"] = selected[:]

            if idx == n:
                return

            upper_bound = current_value + sum(
                weights[nodes[i]]
                for i in range(idx, n)
                if i not in excluded
            )
            if upper_bound <= best["value"]:
                return

            state = (idx, frozenset(excluded))
            if state in memo and memo[state] >= current_value:
                return
            memo[state] = current_value

            for i in range(idx, n):
                if i in excluded:
                    continue
                new_excluded = excluded | conflict_map[i]
                selected.append(i)
                dfs(i + 1, selected, current_value + weights[nodes[i]], new_excluded)
                selected.pop()

        dfs(0, [], 0, set())

        selected_ids = isolated + [nodes[i] for i in best["subset"]]
        total_benefit = isolated_benefit + best["value"]

        elapsed_ms = (time.perf_counter() - start) * 1000
        return SolverResult(
            selected_ids=selected_ids,
            total_benefit=total_benefit,
            execution_time_ms=elapsed_ms,
            recursion_count=recursion_count,
        )