# backend/services/mwis/benchmark.py

from __future__ import annotations

import tracemalloc
from dataclasses import dataclass
from uuid import UUID

from services.mwis.base_solver import BaseMWISSolver, SolverResult


@dataclass(frozen=True)
class BenchmarkResult:
    solver_name: str
    result: SolverResult
    peak_memory_kb: float


def run_benchmark(
    solvers: list[BaseMWISSolver],
    adjacency_list: dict[UUID, set[UUID]],
    weights: dict[UUID, int],
) -> list[BenchmarkResult]:
    results = []

    for solver in solvers:
        tracemalloc.start()
        result = solver.solve(adjacency_list, weights)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results.append(BenchmarkResult(
            solver_name=solver.__class__.__name__,
            result=result,
            peak_memory_kb=peak / 1024,
        ))

    return results


def print_report(results: list[BenchmarkResult]) -> None:
    print(f"\n{'solver':<25} {'수혜액':>15} {'시간(ms)':>12} {'재귀횟수':>10} {'메모리(KB)':>12}")
    print("-" * 80)
    for r in results:
        print(
            f"{r.solver_name:<25}"
            f"{r.result.total_benefit:>15,}"
            f"{r.result.execution_time_ms:>12.2f}"
            f"{r.result.recursion_count:>10,}"
            f"{r.peak_memory_kb:>12.1f}"
        )


if __name__ == "__main__":
    from sqlalchemy.orm import Session
    from database import engine
    from models import Policy
    from services.mwis.graph_builder import build_graph

    from services.mwis.solvers.stage_a_naive import BruteForceSolver
    from services.mwis.solvers.stage_b_dp import DPDFSSolver
    from services.mwis.solvers.stage_c_1_bnb import BranchAndBoundSolver
    from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver
    from services.mwis.solvers.stage_c_3_clique import ComplementGraphCliqueSolver


    # 1. DB에서 정책 데이터 가져오기 -> 현재 30개
    with Session(engine) as db:
        policies = db.query(Policy).limit(30).all()
        
    print(f"[*] DB에서 {len(policies)}개의 정책을 불러왔습니다.")

    # 2. 그래프 빌드
    adjacency_list, weights = build_graph(policies)
    print(f"[*] 그래프 생성 완료 (노드: {len(adjacency_list)}개)")

    # 3. 5개 알고리즘 장전
    solvers = [
        # BruteForceSolver(),
        DPDFSSolver(),
        PreprocessSolver(),
        BranchAndBoundSolver(),
        ComplementGraphCliqueSolver(),
    ]

    # 4. 벤치마크 실행 및 결과 출력
    print("[*] 5개 알고리즘 벤치마크 테스트를 시작합니다...")
    results = run_benchmark(solvers, adjacency_list, weights)
    print_report(results)