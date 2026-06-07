from __future__ import annotations

import statistics
from itertools import combinations
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.profile_schema import UserProfileRequest
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_a_naive import BruteForceSolver
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.mwis.solvers.stage_c_1_bnb import BranchAndBoundSolver
from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver
from services.mwis.solvers.stage_c_3_clique import ComplementGraphCliqueSolver
from services.policy_filter import filter_policies

router = APIRouter(prefix="/verify", tags=["Verification"])

MAX_N_BRUTE = 16

_SOLVERS = [
    ("Stage A",   BruteForceSolver()),
    ("Stage B",   DPDFSSolver()),
    ("Stage C-1", BranchAndBoundSolver()),
    ("Stage C-2", PreprocessSolver()),
    ("Stage C-3", ComplementGraphCliqueSolver()),
]

_TEST_PROFILES = [
    UserProfileRequest(age=25, income_level=0.6, is_employed=False, region="서울"),
    UserProfileRequest(age=22, income_level=0.4, is_employed=False, region="서울"),
    UserProfileRequest(age=28, income_level=0.8, is_employed=True,  region="전국"),
    UserProfileRequest(age=26, income_level=0.5, is_employed=False, region="전국"),
]

_PROFILE_LABELS = [
    "25세 / 미취업 / 서울 / 소득 60%",
    "22세 / 미취업 / 서울 / 소득 40%",
    "28세 / 취업   / 전국 / 소득 80%",
    "26세 / 미취업 / 전국 / 소득 50%",
]


def _enumerate_valid_combinations(adjacency_list: dict, weights: dict) -> list[dict]:
    nodes = list(weights)
    result = []
    for r in range(1, len(nodes) + 1):
        for subset in combinations(nodes, r):
            s = set(subset)
            if all(not (adjacency_list.get(n, set()) & s) for n in subset):
                result.append({
                    "ids": list(subset),
                    "benefit": sum(weights[n] for n in subset),
                })
    return result


# ② 교차 솔버
@router.get("/cross-solver")
def cross_solver(db: Session = Depends(get_db)) -> dict[str, Any]:
    """5개 솔버 교차 검증 — Stage A(전수탐색 기준값) 대비 B·C 일치 여부"""
    rows = []

    for profile, label in zip(_TEST_PROFILES, _PROFILE_LABELS):
        candidates, _ = filter_policies(db, profile)
        if not candidates:
            continue
        adj, w = build_graph(candidates, income_level=profile.income_level)
        n = len(candidates)

        solver_results: list[dict[str, Any]] = []
        stage_a_benefit = None

        for name, solver in _SOLVERS:
            if name == "Stage A" and n > MAX_N_BRUTE:
                solver_results.append({"name": name, "benefit": None, "ms": None, "skipped": True})
                continue
            r = solver.solve(adj, w)
            if name == "Stage A":
                stage_a_benefit = r.total_benefit
            solver_results.append({
                "name": name,
                "benefit": r.total_benefit,
                "ms": round(r.execution_time_ms, 2),
                "skipped": False,
            })

        ref_name = "Stage A" if stage_a_benefit is not None else "Stage B"
        ref = next(s["benefit"] for s in solver_results if s["name"] == ref_name and not s["skipped"])
        for s in solver_results:
            s["match"] = None if s["skipped"] else (s["benefit"] == ref)

        non_skipped = [s for s in solver_results if not s["skipped"]]
        all_match = len(non_skipped) > 0 and all(s["match"] for s in non_skipped)

        rows.append({
            "profile": label,
            "n_candidates": n,
            "search_space": 2 ** n,
            "solvers": solver_results,
            "all_match": all_match,
            "stage_a_skipped": stage_a_benefit is None,
            "reference": ref_name,
        })

    total_compared = sum(len([s for s in r["solvers"] if not s["skipped"]]) for r in rows)
    mismatch_count = sum(
        1 for r in rows for s in r["solvers"]
        if not s["skipped"] and s["match"] is False
    )

    return {
        "rows": rows,
        "summary": {
            "total_compared": total_compared,
            "mismatch_count": mismatch_count,
            "all_match": mismatch_count == 0,
        }
    }


# ② 산점도
@router.get("/distribution")
def distribution(profile_idx: int = 0, db: Session = Depends(get_db)) -> dict[str, Any]:
    """전체 유효 독립 집합 산점도 — 프로필 선택 가능"""
    if profile_idx < 0 or profile_idx >= len(_TEST_PROFILES):
        profile_idx = 0
    profile = _TEST_PROFILES[profile_idx]
    label   = _PROFILE_LABELS[profile_idx]
    candidates, _ = filter_policies(db, profile)

    if not candidates:
        return {"points": [], "optimal": 0, "total_valid": 0, "n_candidates": 0, "capped": False}

    adj, w = build_graph(candidates, income_level=profile.income_level)
    policy_map = {p.id: p.title for p in candidates}

    capped = False
    if len(candidates) > 20:
        top_ids = sorted(w, key=lambda n: w[n], reverse=True)[:20]
        adj = {n: adj[n] & set(top_ids) for n in top_ids}
        w   = {n: w[n] for n in top_ids}
        capped = True

    mwis_result = DPDFSSolver().solve(adj, w)
    all_combos  = _enumerate_valid_combinations(adj, w)

    if not all_combos:
        return {"points": [], "optimal": mwis_result.total_benefit,
                "total_valid": 0, "n_candidates": len(candidates), "capped": capped}

    all_combos.sort(key=lambda c: c["benefit"])
    all_benefits = [c["benefit"] for c in all_combos]

    mean_val   = int(sum(all_benefits) / len(all_benefits))
    median_val = int(statistics.median(all_benefits))
    mean_ratio = round(mwis_result.total_benefit / mean_val, 2) if mean_val > 0 else None

    optimal_set = frozenset(mwis_result.selected_ids)

    points = [
        {
            "x": i,
            "benefit": c["benefit"],
            "policies": [policy_map.get(pid, str(pid)) for pid in c["ids"]],
            "is_optimal": frozenset(c["ids"]) == optimal_set,
        }
        for i, c in enumerate(all_combos)
    ]

    return {
        "points": points,
        "optimal": mwis_result.total_benefit,
        "optimal_policies": [policy_map.get(pid, str(pid)) for pid in mwis_result.selected_ids],
        "total_valid": len(all_combos),
        "n_candidates": len(candidates),
        "profile_label": label,
        "capped": capped,
        "stats": {
            "mean": mean_val,
            "median": median_val,
            "mean_ratio": mean_ratio,
        }
    }