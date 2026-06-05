from __future__ import annotations

from itertools import combinations
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.policy import Policy
from schemas.profile_schema import UserProfileRequest
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_a_naive import BruteForceSolver
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.mwis.solvers.stage_c_1_bnb import BranchAndBoundSolver
from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver
from services.mwis.solvers.stage_c_3_clique import ComplementGraphCliqueSolver
from services.policy_filter import filter_policies

router = APIRouter(prefix="/verify", tags=["Verification"])

MAX_N_BRUTE = 16  # BruteForce 후보 상한 (초과 시 stage_a 생략)

_SOLVERS = [
    ("Stage A",   BruteForceSolver()),
    ("Stage B",   DPDFSSolver()),
    ("Stage C-1", BranchAndBoundSolver()),
    ("Stage C-2", PreprocessSolver()),
    ("Stage C-3", ComplementGraphCliqueSolver()),
]


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _greedy_solve(adjacency_list: dict, weights: dict) -> tuple[list, int]:
    """가중치 내림차순 그리디 — 비교 기준선"""
    sorted_nodes = sorted(weights, key=lambda n: weights[n], reverse=True)
    selected, excluded = [], set()
    for node in sorted_nodes:
        if node not in excluded:
            selected.append(node)
            excluded.update(adjacency_list.get(node, set()))
    return selected, sum(weights[n] for n in selected)


def _enumerate_valid_benefits(adjacency_list: dict, weights: dict) -> list[int]:
    """모든 유효 독립 집합의 수혜액 목록 — O(2^N), N<=20 권장"""
    nodes = list(weights)
    benefits = []
    for r in range(1, len(nodes) + 1):
        for subset in combinations(nodes, r):
            s = set(subset)
            if all(not (adjacency_list.get(n, set()) & s) for n in subset):
                benefits.append(sum(weights[n] for n in subset))
    return benefits


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


# ---------------------------------------------------------------------------
# ① Adversarial Case
# ---------------------------------------------------------------------------

@router.get("/adversarial")
def adversarial_case(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Greedy vs MWIS — finance 클러스터 실데이터"""
    finance_policies = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(
            Policy.is_active == True,
            Policy.is_supplementary == False,
            Policy.category == "finance",
        )
        .all()
    )

    if not finance_policies:
        return {"policies": [], "exclusive_edges": [],
                "greedy": {"selected": [], "total_benefit": 0},
                "mwis":   {"selected": [], "total_benefit": 0}}

    income_level = 0.6
    adjacency_list, weights = build_graph(finance_policies, income_level=income_level)

    greedy_ids, greedy_benefit = _greedy_solve(adjacency_list, weights)
    mwis_result = DPDFSSolver().solve(adjacency_list, weights)

    policy_map = {p.id: p.title for p in finance_policies}

    return {
        "policies": sorted(
            [{"title": p.title, "weight": weights.get(p.id, 0)}
             for p in finance_policies if weights.get(p.id, 0) > 0],
            key=lambda x: x["weight"],
            reverse=True,
        ),
        "exclusive_edges": [
            [policy_map[u], policy_map[v]]
            for u, neighbors in adjacency_list.items()
            for v in neighbors
            if u < v and u in policy_map and v in policy_map
        ],
        "greedy": {
            "selected": [policy_map[pid] for pid in greedy_ids if pid in policy_map],
            "total_benefit": greedy_benefit,
        },
        "mwis": {
            "selected": [policy_map[pid] for pid in mwis_result.selected_ids if pid in policy_map],
            "total_benefit": mwis_result.total_benefit,
        },
    }


# ---------------------------------------------------------------------------
# ② 교차 솔버
# ---------------------------------------------------------------------------

@router.get("/cross-solver")
def cross_solver(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """5개 솔버 교차 검증 — 4개 프로필 × (Stage A·B·C-1·C-2·C-3)"""
    results = []

    for profile, label in zip(_TEST_PROFILES, _PROFILE_LABELS):
        candidates, _ = filter_policies(db, profile)
        if not candidates:
            continue
        adj, w = build_graph(candidates, income_level=profile.income_level)
        n = len(candidates)

        solver_results: list[dict[str, Any]] = []
        for name, solver in _SOLVERS:
            if name == "Stage A" and n > MAX_N_BRUTE:
                solver_results.append({"name": name, "benefit": None, "ms": None, "skipped": True})
                continue
            r = solver.solve(adj, w)
            solver_results.append({
                "name": name,
                "benefit": r.total_benefit,
                "ms": round(r.execution_time_ms, 2),
                "skipped": False,
            })

        # Stage B를 기준으로 일치 여부 판정 (항상 실행됨)
        ref = next(s["benefit"] for s in solver_results if s["name"] == "Stage B")
        for s in solver_results:
            s["match"] = None if s["skipped"] else (s["benefit"] == ref)

        non_skipped = [s for s in solver_results if not s["skipped"]]
        all_match = len(non_skipped) > 0 and all(s["match"] for s in non_skipped)

        results.append({
            "profile": label,
            "n_candidates": n,
            "solvers": solver_results,
            "all_match": all_match,
            "stage_a_skipped": n > MAX_N_BRUTE,
        })

    return results


# ---------------------------------------------------------------------------
# ③ 분포 히스토그램
# ---------------------------------------------------------------------------

@router.get("/distribution")
def distribution(db: Session = Depends(get_db)) -> dict[str, Any]:
    """전체 유효 독립 집합 수혜액 분포 + MWIS 최적값"""
    profile = UserProfileRequest(age=25, income_level=0.6, is_employed=False, region="서울")
    candidates, _ = filter_policies(db, profile)

    if not candidates:
        return {"bins": [], "optimal": 0, "optimal_bin": 0,
                "total_valid": 0, "n_candidates": 0, "capped": False}

    adj, w = build_graph(candidates, income_level=0.6)

    # 조합 폭발 방지: N>20이면 가중치 상위 20개만 사용
    capped = False
    if len(candidates) > 20:
        top_ids = sorted(w, key=lambda n: w[n], reverse=True)[:20]
        adj = {n: adj[n] & set(top_ids) for n in top_ids}
        w   = {n: w[n] for n in top_ids}
        capped = True

    # mwis_result과 all_benefits는 항상 동일한 adj/w 기반으로 계산
    mwis_result  = DPDFSSolver().solve(adj, w)
    all_benefits = _enumerate_valid_benefits(adj, w)

    if not all_benefits:
        return {"bins": [], "optimal": mwis_result.total_benefit, "optimal_bin": 0,
                "total_valid": 0, "n_candidates": len(candidates), "capped": capped}

    min_b, max_b = min(all_benefits), max(all_benefits)
    bin_size = max(1, (max_b - min_b) // 20)

    freq: dict[int, int] = {}
    for b in all_benefits:
        key = (b // bin_size) * bin_size
        freq[key] = freq.get(key, 0) + 1

    optimal_bin = (mwis_result.total_benefit // bin_size) * bin_size

    return {
        "bins": [{"x": k, "y": v} for k, v in sorted(freq.items())],
        "optimal": mwis_result.total_benefit,
        "optimal_bin": optimal_bin,
        "total_valid": len(all_benefits),
        "n_candidates": len(candidates),
        "profile_label": "25세 / 미취업 / 서울 / 소득 60%",
        "capped": capped,
    }