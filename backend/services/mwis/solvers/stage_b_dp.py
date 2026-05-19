# stage_b_dp.py
import time
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult


class DPDFSSolver(BaseMWISSolver):
    """
    Stage B: DP + DFS 백트래킹
    시간복잡도: worst case O(2^N), 평균적으로 훨씬 빠름
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        start = time.perf_counter()

        nodes = list(adjacency_list.keys())
        n = len(nodes)
        idx_map = {node_id: i for i, node_id in enumerate(nodes)}

        conflict_map: list[set] = []
        for node_id in nodes:
            conflicts = {idx_map[nb] for nb in adjacency_list[node_id] if nb in idx_map}
            conflict_map.append(conflicts)

        best = {"value": 0, "subset": []}
        memo: dict = {}
        recursion_count = 0

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

        elapsed_ms = (time.perf_counter() - start) * 1000
        return SolverResult(
            selected_ids=[nodes[i] for i in best["subset"]],
            total_benefit=best["value"],
            execution_time_ms=elapsed_ms,
            recursion_count=recursion_count,
        )