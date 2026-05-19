"""
base_solver.py
==============

MWIS(Maximum Weight Independent Set) 알고리즘 전략 패턴의 '공통 규격서'.

이 모듈이 존재하는 이유
-----------------------
향후 구현될 5가지 알고리즘(Brute-Force, Greedy, DP, Branch & Bound,
근사 알고리즘 등)은 각기 다른 시간·공간 복잡도 트레이드오프를 가진다.
이 추상 클래스는 그 모든 구현체가 **동일한 입출력 계약**을 따르도록
강제함으로써 다음 두 가지 설계 목표를 동시에 달성한다.

1. **교체 가능성(Substitutability)**:
   FastAPI 엔드포인트, 벤치마크 러너, 테스트 코드가 어느 구현체인지
   알 필요 없이 ``BaseMWISSolver`` 타입 하나만 의존하면 된다.
   전략을 교체해도 호출부 코드는 단 한 줄도 바뀌지 않는다.

2. **정량적 벤치마크 통일성(Comparable Metrics)**:
   모든 구현체가 동일한 :class:`SolverResult` 를 반환하므로,
   알고리즘 간 실행 시간·재귀 호출 횟수·최적해 품질을 공정하게
   비교하는 벤치마크 레포트를 별도 어댑터 없이 바로 생성할 수 있다.

하위 클래스 구현 가이드
-----------------------
::

    from uuid import UUID
    from backend.services.mwis.base_solver import BaseMWISSolver, SolverResult

    class MyGreedySolver(BaseMWISSolver):
        \"\"\"가중치 내림차순 그리디 MWIS 구현체.\"\"\"

        def solve(
            self,
            adjacency_list: dict[UUID, set[UUID]],
            weights: dict[UUID, int],
        ) -> SolverResult:
            import time
            start = time.perf_counter()

            # --- 알고리즘 구현 ---
            selected: list[UUID] = []
            ...

            elapsed_ms = (time.perf_counter() - start) * 1000
            return SolverResult(
                selected_ids=selected,
                total_benefit=sum(weights[n] for n in selected),
                execution_time_ms=elapsed_ms,
                recursion_count=0,   # 반복문 기반이므로 0
            )

주의사항
--------
- ``solve`` 는 **순수 함수적**으로 동작해야 한다. 입력 ``adjacency_list``
  와 ``weights`` 를 절대 변경(mutate)하지 말 것. 필요하면 내부에서 복사.
- 입력 그래프는 :mod:`graph_builder` 의 불변식을 이미 만족한다고 가정한다.
  (무방향, 고립 노드 보존, dangling 간선 제거) 하위 클래스에서
  재검증하지 않아도 된다.
- ``recursion_count`` 는 실제 재귀 호출마다 1씩 누적해야 한다.
  반복문(iterative) 기반 구현은 0 을 그대로 두면 된다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

__all__ = ["SolverResult", "BaseMWISSolver"]


# ---------------------------------------------------------------------------
# 벤치마크 결과 구조체
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SolverResult:
    """MWIS 알고리즘 한 번의 실행 결과를 담는 불변 값 객체(Value Object).

    ``frozen=True`` 로 선언하여 반환 이후 외부에서 수치를 수정하는
    실수를 컴파일 타임(타입 체커) 수준에서 차단한다.
    벤치마크 레포트가 이 객체를 리스트로 수집·비교하기 때문에
    불변성은 결과의 신뢰성을 보장하는 핵심 속성이다.

    Attributes
    ----------
    selected_ids:
        독립 집합으로 선택된 정책 UUID 목록.
        MWIS 관점에서 "중복 수혜 없이 동시에 신청 가능한 정책들"이다.
        순서는 알고리즘 구현에 따라 달라질 수 있으므로 의미를 부여하지 말 것.
    total_benefit:
        선택된 정책들의 ``total_benefit`` 합산액(원 단위).
        ``sum(weights[n] for n in selected_ids)`` 와 일치해야 한다.
    execution_time_ms:
        ``solve`` 진입부터 반환 직전까지의 벽시계(wall-clock) 실행 시간.
        ``time.perf_counter()`` 기반으로 밀리초(ms) 단위로 기록한다.
        벤치마크의 1차 비교 지표다.
    recursion_count:
        재귀 호출이 발생한 총 횟수. 재귀 기반 알고리즘(Brute-Force,
        Branch & Bound 등)에서 탐색 공간 크기를 정량화하는 지표다.
        반복문(iterative) 기반 구현은 ``0`` 으로 두면 된다.

    Examples
    --------
    >>> from uuid import uuid4
    >>> r = SolverResult(
    ...     selected_ids=[uuid4()],
    ...     total_benefit=500_000,
    ...     execution_time_ms=1.23,
    ...     recursion_count=0,
    ... )
    >>> r.total_benefit
    500000
    """

    selected_ids: list[UUID]
    total_benefit: int
    execution_time_ms: float
    recursion_count: int = field(default=0)


# ---------------------------------------------------------------------------
# 추상 베이스 클래스 — 전략 패턴의 공통 인터페이스
# ---------------------------------------------------------------------------
class BaseMWISSolver(ABC):
    """MWIS 알고리즘 구현체가 반드시 준수해야 하는 공통 규격서.

    이 클래스를 직접 인스턴스화할 수 없다. ``solve`` 를 구현하지 않은 채
    인스턴스를 생성하려 하면 ``TypeError`` 가 즉시 발생한다.

    전략 패턴 관계도
    ----------------
    ::

        BaseMWISSolver          ← 이 파일 (인터페이스/계약)
        ├── BruteForceSolver    ← Stage A: 정확해, 지수 시간
        ├── GreedySolver        ← Stage A: 근사해, 선형 시간
        ├── DPSolver            ← Stage B: 트리 DP (Chordal graph 한정)
        ├── BranchAndBoundSolver← Stage B: 정확해, 가지치기로 탐색 축소
        └── ApproximateSolver   ← Stage C: PTAS 또는 LP 기반 근사

    벤치마크 러너 사용 예시
    -----------------------
    ::

        solvers: list[BaseMWISSolver] = [
            BruteForceSolver(),
            GreedySolver(),
            DPSolver(),
        ]
        for solver in solvers:
            result: SolverResult = solver.solve(adjacency_list, weights)
            print(f"{solver.__class__.__name__}: "
                  f"{result.total_benefit}원 / "
                  f"{result.execution_time_ms:.3f}ms / "
                  f"재귀 {result.recursion_count}회")

    Notes
    -----
    - 이 클래스는 상태(state)를 가지지 않는다. 구현체도 가급적 무상태로
      설계해 동시 요청 환경(FastAPI async)에서 인스턴스를 재사용할 수 있게 할 것.
    - 입력 그래프는 :func:`~backend.services.mwis.graph_builder.build_graph`
      를 통과한 정규화된 자료구조임을 전제한다.
    """

    @abstractmethod
    def solve(
        self,
        adjacency_list: dict[UUID, set[UUID]],
        weights: dict[UUID, int],
    ) -> SolverResult:
        """MWIS 문제를 풀고 결과를 반환하는 핵심 진입점.

        **이 메서드의 계약(Contract)**

        - *사전 조건(Precondition)*:
            - ``adjacency_list`` 의 모든 키는 ``weights`` 에도 키로 존재한다.
            - 그래프는 무방향이다: ``v in adjacency_list[u]`` 이면
              ``u in adjacency_list[v]`` 도 반드시 성립한다.
        - *사후 조건(Postcondition)*:
            - 반환된 ``selected_ids`` 내 임의의 두 노드 ``u``, ``v`` 에 대해
              ``v not in adjacency_list[u]`` 가 성립한다. (독립 집합 조건)
            - ``result.total_benefit == sum(weights[n] for n in result.selected_ids)``
        - *부작용 없음(No Side Effects)*:
            - ``adjacency_list`` 와 ``weights`` 를 절대 변경하지 않는다.

        Parameters
        ----------
        adjacency_list:
            ``{정책_id: {배타_정책_id, ...}}`` 형태의 무방향 인접 리스트.
            :func:`~backend.services.mwis.graph_builder.build_graph` 의
            첫 번째 반환값을 그대로 전달한다.
        weights:
            ``{정책_id: total_benefit}`` 형태의 가중치 딕셔너리.
            :func:`~backend.services.mwis.graph_builder.build_graph` 의
            두 번째 반환값을 그대로 전달한다.

        Returns
        -------
        SolverResult
            선택된 정책 ID 목록, 총 수혜 금액, 실행 시간(ms), 재귀 횟수를
            담은 불변 결과 객체.

        Raises
        ------
        NotImplementedError
            이 추상 메서드를 구현하지 않고 호출하면 자동으로 발생한다.
            (ABC 메커니즘이 처리하므로 하위 클래스에서 ``super().solve()``
            를 호출할 필요가 없다.)
        """
        ...
