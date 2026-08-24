"""
data_richness_check.py — 지금 DB에 있는 정책 데이터가 서비스의 핵심 약속
("배타 관계·시계열 환승·숨은 알짜 정책을 놓치지 않게 해준다")을 실제로
얼마나 채우고 있는지 재보는 진단 스크립트.

PDF ETL로 데이터를 늘리기 전에, 지금 상태의 기준선(baseline)을 먼저 잡아둔다.
backend_check.py와 마찬가지로 backend/ 디렉터리에서 실행한다.

    cd backend
    python data_richness_check.py
"""
from __future__ import annotations

import statistics
from datetime import date

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from sqlalchemy.orm import Session, joinedload

from database import engine
from models.policy import Policy
from services.mwis.graph_builder import build_graph
from services.mwis.solvers.stage_b_dp import DPDFSSolver
from services.transition.roadmap_planner import plan_full_roadmap

W = 65
def section(t): print(f"\n{'═'*W}\n  {t}\n{'═'*W}")
def line(label, value): print(f"  {label:<38} {value}")


with Session(engine) as db:
    all_policies = (
        db.query(Policy)
        .options(joinedload(Policy.tiers))
        .filter(Policy.is_active == True)
        .all()
    )

candidates = [p for p in all_policies if not p.is_supplementary]
supplementary = [p for p in all_policies if p.is_supplementary]

section("1. 데이터 규모")
line("전체 활성 정책", f"{len(all_policies)}개")
line("MWIS 후보 (is_supplementary=False)", f"{len(candidates)}개")
line("보조 정책 (is_supplementary=True)", f"{len(supplementary)}개")


section("2. 배타 관계 밀도 — '배타적으로' 약속이 실체가 있는가")
adjacency, weights = build_graph(candidates)
degree = {pid: len(adj) for pid, adj in adjacency.items()}

n = len(degree)
isolated = [pid for pid, d in degree.items() if d == 0]
connected = [pid for pid, d in degree.items() if d > 0]
total_edges = sum(degree.values()) // 2

line("MWIS 후보 노드 수", n)
line("배타 간선(edge) 수", total_edges)
line("고립 노드 (배타 관계 전혀 없음)", f"{len(isolated)}개 ({len(isolated)/n*100:.1f}%)" if n else "N/A")
line("배타 관계에 걸린 노드", f"{len(connected)}개 ({len(connected)/n*100:.1f}%)" if n else "N/A")

isolated_titles = [p.title for p in candidates if p.id in isolated]
print("\n  → 고립 노드(=배타 없음, 항상 자동 선택되는 '숨은 알짜' 후보) 샘플:")
for t in isolated_titles[:8]:
    print(f"      · {t}")
if len(isolated_titles) > 8:
    print(f"      ... 외 {len(isolated_titles)-8}개")


section("3. 시계열 환승 여지 — '환승적으로' 약속이 실체가 있는가")
# 대표 프로필 몇 개로 실제 로드맵을 돌려서 Phase 2(환승 경로)가 채워지는지 확인
PROFILES = [
    ("25세/서울/미취업/소득60%", 25, "서울", False, 0.6),
    ("22세/서울/미취업/소득40%", 22, "서울", False, 0.4),
    ("28세/전국/취업/소득80%",  28, "전국", True,  0.8),
    ("30세/전국/미취업/소득30%", 30, "전국", False, 0.3),
    ("19세/서울/미취업/소득20%", 19, "서울", False, 0.2),
]

phase2_hits = 0
for label, age, region, employed, income in PROFILES:
    pool = [
        p for p in candidates
        if (p.age_min is None or p.age_min <= age)
        and (p.age_max is None or p.age_max >= age)
        and (p.super_region in (None, "전국", region))
    ]
    if not pool:
        print(f"  {label:<28} → 후보 없음")
        continue
    adj, w = build_graph(pool, income_level=income)
    mwis_ids = set(DPDFSSolver().solve(adj, w).selected_ids)
    roadmap = plan_full_roadmap(
        all_mwis_policies=pool, mwis_ids=mwis_ids,
        user_start=date.today(), income_level=income,
        gap_days=14, horizon_months=60,
    )
    has_phase2 = any(ph.label.startswith("환승") for ph in roadmap.phases)
    if has_phase2:
        phase2_hits += 1
    print(f"  {label:<28} → 후보 {len(pool):>3}개, Phase 수 {len(roadmap.phases)}, "
          f"환승경로 {'있음' if has_phase2 else '없음'}")

line("샘플 프로필 중 환승 경로가 실제로 나온 비율", f"{phase2_hits}/{len(PROFILES)}")


section("요약")
print(f"""
  이 숫자들이 낮으면(예: 고립 노드가 90%+, 환승 경로 0/5) 지금 데이터로는
  MWIS·DAG-DP 알고리즘이 있어도 사용자가 체감할 '복잡한 걸 대신 풀어준다'는
  가치가 크지 않다는 뜻 — PDF ETL로 정책 수·배타관계·시계열 다양성을
  늘리는 작업의 우선순위를 뒷받침하는 근거가 됩니다.
""")
