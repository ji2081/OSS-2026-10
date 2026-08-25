"""
base_solver.py

MWIS(Maximum Weight Independent Set) 솔버들의 공통 인터페이스.
Stage A~C의 모든 구현체는 BaseMWISSolver를 상속하고 SolverResult를 반환한다.

- adjacency_list: {정책_id: {배타_정책_id, ...}} 형태의 무방향 인접 리스트
- weights: {정책_id: total_benefit}
- 반환되는 selected_ids는 독립 집합(서로 배타 관계 없음)이어야 한다.
- solve()는 입력을 변경하지 않는 순수 함수여야 한다.
- recursion_count: 재귀 기반 알고리즘은 호출마다 누적, 반복문 기반은 0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

__all__ = ["SolverResult", "BaseMWISSolver"]


@dataclass(frozen=True)
class SolverResult:
    """MWIS 알고리즘 1회 실행 결과.

    selected_ids: 독립 집합으로 선택된 정책 UUID 목록
    total_benefit: 선택된 정책들의 total_benefit 합산액 (원), sum(weights[n] for n in selected_ids)와 일치해야 함
    execution_time_ms: solve() 실행 시간 (ms, time.perf_counter 기준)
    recursion_count: 재귀 호출 횟수 (반복문 기반 구현은 0)
    """
    selected_ids: list[UUID]
    total_benefit: int
    execution_time_ms: float
    recursion_count: int = field(default=0)


class BaseMWISSolver(ABC):
    """MWIS 솔버 구현체의 공통 인터페이스 (전략 패턴).

    입력 그래프는 graph_builder.build_graph()를 통과한 정규화된
    자료구조(무방향, dangling 간선 제거됨)임을 전제한다.
    """

    @abstractmethod
    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        """MWIS 문제를 풀고 SolverResult를 반환한다.

        adjacency_list, weights를 변경하지 않는다(순수 함수).
        반환된 selected_ids 내 임의의 두 노드는 서로 adjacency_list에
        포함되지 않아야 하며(독립 집합 조건),
        total_benefit == sum(weights[n] for n in selected_ids)여야 한다.
        """