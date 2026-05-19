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

    with Session(engine) as db:
        policies = db.query(Policy).filter(
            Policy.is_active == True,
            Policy.total_benefit.isnot(None)
        ).all()

    adjacency, weights = build_graph(policies)
    results = run_benchmark(
        solvers=[BruteForceSolver(), DPDFSSolver()],
        adjacency_list=adjacency,
        weights=weights,
    )
    print_report(results)