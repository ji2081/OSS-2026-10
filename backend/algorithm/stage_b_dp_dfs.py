# algorithm/stage_b_dp_dfs.py

from typing import List, Dict, Tuple

def solve_mwis_dp_dfs(policies: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Stage B: DP + DFS 백트래킹
    - 충돌 경로 가지치기(Pruning): 배타 조건 위반 시 즉시 해당 노드 제거
    - 상위 연산 메모이제이션(DP): 중복 연산 방지
    - 시간복잡도: worst case O(2^N), 평균적으로 훨씬 빠름
    """
    n = len(policies)
    title_to_idx = {p["title"]: i for i, p in enumerate(policies)}

    # 배타 관계를 인덱스 집합으로 변환
    conflict_map: List[set] = []
    for p in policies:
        conflicts = set()
        for exc in p.get("exclusive_with", []):
            if exc in title_to_idx:
                conflicts.add(title_to_idx[exc])
        conflict_map.append(conflicts)

    best = {"value": 0, "subset": []}
    memo = {}

    def dfs(idx: int, selected: List[int], current_value: int, excluded: set):
        nonlocal best

        if current_value > best["value"]:
            best["value"] = current_value
            best["subset"] = selected[:]

        if idx == n:
            return

        # 상한선 가지치기: 남은 정책 전부 더해도 현재 best 못 넘으면 중단
        upper_bound = current_value + sum(
            (policies[i].get("total_benefit") or 0)
            for i in range(idx, n)
            if i not in excluded
        )
        if upper_bound <= best["value"]:
            return

        # 메모이제이션 키: (현재 인덱스, 선택된 집합)
        state = (idx, frozenset(excluded))
        if state in memo and memo[state] >= current_value:
            return
        memo[state] = current_value

        for i in range(idx, n):
            if i in excluded:
                continue

            benefit = policies[i].get("total_benefit") or 0
            new_excluded = excluded | conflict_map[i]

            selected.append(i)
            dfs(i + 1, selected, current_value + benefit, new_excluded)
            selected.pop()

    dfs(0, [], 0, set())

    return [policies[i] for i in best["subset"]], best["value"]