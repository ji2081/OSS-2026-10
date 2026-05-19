# algorithm/stage_a_naive.py

from itertools import combinations
from typing import List, Dict, Tuple

def solve_mwis_naive(policies: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Stage A: Naive 완전 탐색
    모든 부분집합을 순회하며 배타 조건 위반 없는 최대 가중치 집합 탐색
    시간복잡도: O(2^N)
    """
    n = len(policies)
    best_value = 0
    best_subset = []

    for r in range(1, n + 1):
        for subset in combinations(range(n), r):
            if _is_valid(subset, policies) and (value := _total_benefit(subset, policies)) > best_value:
                best_value = value
                best_subset = [policies[i] for i in subset]

    return best_subset, best_value


def _is_valid(subset: tuple, policies: List[Dict]) -> bool:
    titles_in_subset = {policies[i]["title"] for i in subset}
    for i in subset:
        for excluded in policies[i].get("exclusive_with", []):
            if excluded in titles_in_subset:
                return False
    return True


def _total_benefit(subset: tuple, policies: List[Dict]) -> int:
    return sum(policies[i].get("total_benefit") or 0 for i in subset)