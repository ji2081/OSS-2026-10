# stage_a_naive.py
import time
from itertools import combinations
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult


class BruteForceSolver(BaseMWISSolver):
    """
    Stage A: 완전 탐색
    시간복잡도: O(2^N)
    """

    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        start = time.perf_counter()

        nodes = list(adjacency_list.keys())
        n = len(nodes)
        best_ids: list[UUID] = []
        best_value = 0
        recursion_count = 0

        for r in range(1, n + 1):
            for subset in combinations(range(n), r):
                recursion_count += 1
                if self._is_valid(subset, nodes, adjacency_list):
                    value = sum(weights[nodes[i]] for i in subset)
                    if value > best_value:
                        best_value = value
                        best_ids = [nodes[i] for i in subset]

        elapsed_ms = (time.perf_counter() - start) * 1000
        return SolverResult(
            selected_ids=best_ids,
            total_benefit=best_value,
            execution_time_ms=elapsed_ms,
            recursion_count=recursion_count,
        )

    def _is_valid(
        self,
        subset: tuple,
        nodes: list[UUID],
        adjacency_list: dict[UUID, set[UUID]],
    ) -> bool:
        ids_in_subset = {nodes[i] for i in subset}
        for i in subset:
            if adjacency_list[nodes[i]] & ids_in_subset:
                return False
        return True