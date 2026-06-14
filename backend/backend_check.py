from __future__ import annotations
import sys, os, json, traceback
from datetime import date

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

W = 65
def section(t): print(f"\n{'═'*W}\n  {t}\n{'═'*W}")
def ok(m):   print(f"  ✅  {m}")
def fail(m): print(f"  ❌  {m}")
def warn(m): print(f"  ⚠️   {m}")
def info(m): print(f"  ℹ️   {m}")
def hr():    print(f"  {'─'*60}")

results: dict[str, bool] = {}

# ── 공통 imports (최상단에서 한 번만) ─────────────────────────────
try:
    from sqlalchemy.orm import Session, joinedload
    from database import engine
    from models.policy import Policy, PolicyTier
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    _db_err = str(e)

# ─────────────────────────────────────────────────────────────────
# 1. Import 검증
# ─────────────────────────────────────────────────────────────────
section("1 / 7  Import 검증")

def chk(label, mod):
    try:
        __import__(mod); ok(label); return True
    except Exception as e:
        fail(f"{label} → {e}"); return False

results["imports"] = all([
    chk("sqlalchemy",                      "sqlalchemy"),
    chk("database",                        "database"),
    chk("models.policy",                   "models.policy"),
    chk("services.mwis.graph_builder",     "services.mwis.graph_builder"),
    chk("services.mwis.solvers.stage_a",   "services.mwis.solvers.stage_a_naive"),
    chk("services.mwis.solvers.stage_b",   "services.mwis.solvers.stage_b_dp"),
    chk("services.mwis.solvers.stage_c1",  "services.mwis.solvers.stage_c_1_bnb"),
    chk("services.mwis.solvers.stage_c2",  "services.mwis.solvers.stage_c_2_preprocess"),
    chk("services.mwis.solvers.stage_c3",  "services.mwis.solvers.stage_c_3_clique"),
    chk("services.transition.roadmap_planner", "services.transition.roadmap_planner"),
    chk("schemas.roadmap_schema",          "schemas.roadmap_schema"),
    chk("routers.roadmap_router",          "routers.roadmap_router"),
])

# ─────────────────────────────────────────────────────────────────
# 2. DB 연결 + 데이터 현황
# ─────────────────────────────────────────────────────────────────
section("2 / 7  DB 연결 + 데이터 현황")

if not DB_AVAILABLE:
    fail(f"DB 모듈 로드 실패: {_db_err}")
    fail("venv 활성화 여부 확인: source venv/Scripts/activate")
    results["db"] = False
else:
    try:
        with Session(engine) as db:
            total      = db.query(Policy).count()
            active     = db.query(Policy).filter(Policy.is_active==True).count()
            candidates = db.query(Policy).filter(Policy.is_active==True, Policy.is_supplementary==False).count()
            supp       = db.query(Policy).filter(Policy.is_active==True, Policy.is_supplementary==True).count()
            has_tiers  = db.query(Policy).filter(Policy.is_active==True, Policy.is_supplementary==False).join(PolicyTier).distinct().count()
            tier_total = db.query(PolicyTier).count()

        no_tiers = candidates - has_tiers
        ok("DB 연결 성공")
        info(f"전체 정책: {total}개  (활성: {active}개)")
        info(f"MWIS 후보: {candidates}개  |  보조정책: {supp}개")
        info(f"tiers 있음: {has_tiers}개  |  tiers 없음(weight=0): {no_tiers}개")
        info(f"policy_tiers 총 레코드: {tier_total}개")
        if no_tiers > 0:
            warn(f"tiers 없는 MWIS 후보 {no_tiers}개 → MWIS에서 가중치 0 처리됨")
        results["db"] = True
    except Exception as e:
        fail(f"DB 쿼리 실패: {e}"); results["db"] = False

# ─────────────────────────────────────────────────────────────────
# 3. graph_builder WINDOW 경계
# ─────────────────────────────────────────────────────────────────
section("3 / 7  graph_builder WINDOW 경계 점검")

try:
    import services.mwis.graph_builder as gb
    ws, we, today = gb.WINDOW_START, gb.WINDOW_END, date.today()
    info(f"WINDOW_START={ws}  WINDOW_END={we}  오늘={today}")

    if today > we:
        fail(f"WINDOW_END가 과거 → 모든 weight=0 위험!")
        results["window"] = False
    else:
        remaining = (we - today).days
        (ok if remaining > 60 else warn)(f"WINDOW 정상, {remaining}일 남음")
        results["window"] = True

    if DB_AVAILABLE:
        with Session(engine) as db:
            sample = (db.query(Policy).options(joinedload(Policy.tiers))
                      .filter(Policy.is_active==True, Policy.is_supplementary==False)
                      .limit(5).all())
        adj, weights = gb.build_graph(sample)
        zeros   = [p.title for p in sample if weights.get(p.id, -1) == 0]
        nonzero = [p.title for p in sample if weights.get(p.id,  0) > 0]
        if nonzero: ok(f"가중치 > 0: {nonzero[:2]}")
        if zeros:   warn(f"가중치 = 0: {zeros}")
except Exception as e:
    fail(f"graph_builder 점검 실패: {e}"); results["window"] = False

# ─────────────────────────────────────────────────────────────────
# 4. MWIS 솔버 교차 검증
# ─────────────────────────────────────────────────────────────────
section("4 / 7  MWIS 솔버 교차 검증")

if not DB_AVAILABLE:
    warn("DB 없어서 건너뜀"); results["solvers"] = False
else:
    try:
        from services.mwis.solvers.stage_a_naive        import BruteForceSolver
        from services.mwis.solvers.stage_b_dp           import DPDFSSolver
        from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver

        with Session(engine) as db:
            policies = (db.query(Policy).options(joinedload(Policy.tiers))
                        .filter(Policy.is_active==True, Policy.is_supplementary==False).all())

        adj, weights = gb.build_graph(policies)
        info(f"MWIS 후보 {len(policies)}개")

        ra = BruteForceSolver().solve(adj, weights)
        rb = DPDFSSolver().solve(adj, weights)
        rc = PreprocessSolver().solve(adj, weights)

        print(f"\n  {'솔버':<28} {'수혜액':>14} {'ms':>8} {'재귀':>8}")
        print(f"  {'─'*28} {'─'*14} {'─'*8} {'─'*8}")
        for name, r in [("Stage A  BruteForce",ra),("Stage B  DPDFS",rb),("Stage C2 Preprocess",rc)]:
            print(f"  {name:<28} {r.total_benefit:>14,} {r.execution_time_ms:>8.2f} {r.recursion_count:>8,}")
        hr()

        vals = {ra.total_benefit, rb.total_benefit, rc.total_benefit}
        if len(vals) == 1:
            ok(f"3개 솔버 동일 최적해: {ra.total_benefit:,}원")
            results["solvers"] = True
        else:
            fail(f"솔버 결과 불일치: {vals}"); results["solvers"] = False

    except Exception as e:
        fail(f"솔버 검증 실패: {e}"); traceback.print_exc(); results["solvers"] = False

# ─────────────────────────────────────────────────────────────────
# 5. roadmap_planner E2E
# ─────────────────────────────────────────────────────────────────
section("5 / 7  roadmap_planner E2E 검증")

if not DB_AVAILABLE:
    warn("DB 없어서 건너뜀"); results["roadmap"] = False
else:
    try:
        from services.transition.roadmap_planner import plan_full_roadmap
        from services.mwis.solvers.stage_c_2_preprocess import PreprocessSolver as PS

        with Session(engine) as db:
            policies = (db.query(Policy).options(joinedload(Policy.tiers))
                        .filter(Policy.is_active==True, Policy.is_supplementary==False).all())

        adj, weights = gb.build_graph(policies)
        mwis_ids = set(PS().solve(adj, weights).selected_ids)

        roadmap = plan_full_roadmap(
            all_mwis_policies=policies, mwis_ids=mwis_ids,
            user_start=date.today(), income_level=None,
            gap_days=14, horizon_months=60,
        )

        info(f"Phase 수: {len(roadmap.phases)}개  |  총 수혜액: {roadmap.total_benefit:,}원  |  총 기간: {roadmap.total_months}개월")
        for ph in roadmap.phases:
            print(f"\n    [{ph.label}]  {ph.total_benefit:,}원")
            for iv in ph.policies:
                print(f"      • {iv.title}  ({iv.duration_months}개월, {iv.monthly_benefit:,}원/월)")
        if roadmap.transitions:
            print(f"\n    환승 경로:")
            for f, t in roadmap.transitions:
                print(f"      {f}  →  {t}")
        ok("roadmap_planner 정상 동작")
        results["roadmap"] = True
    except Exception as e:
        fail(f"roadmap_planner 오류: {e}"); traceback.print_exc(); results["roadmap"] = False

# ─────────────────────────────────────────────────────────────────
# 6. main.py 라우터 등록
# ─────────────────────────────────────────────────────────────────
section("6 / 7  main.py 라우터 등록 점검")

try:
    src = open("main.py", encoding="utf-8").read()
    for name in ["policy_router","user_router","result_router","roadmap_router"]:
        (ok if name in src else fail)(f"{name} {'등록됨' if name in src else '미등록 ← include_router 추가 필요'}")
    required = ["policy_router", "user_router", "result_router", "roadmap_router"]
    results["main"] = all(name in src for name in required)
except Exception as e:
    fail(f"main.py 읽기 실패: {e}"); results["main"] = False

# ─────────────────────────────────────────────────────────────────
# 7. 배타 관계 대칭성
# ─────────────────────────────────────────────────────────────────
section("7 / 7  DB 배타 관계 대칭성")

if not DB_AVAILABLE:
    warn("DB 없어서 건너뜀"); results["exclusion"] = False
else:
    try:
        with Session(engine) as db:
            all_p = db.query(Policy).filter(Policy.is_active==True).all()
        id_map = {str(p.id): p for p in all_p}
        asym = []
        for p in all_p:
            raw = p.exclusive_with or []
            if isinstance(raw, str): raw = json.loads(raw)
            for eid in raw:
                t = id_map.get(str(eid))
                if not t: continue
                rev = t.exclusive_with or []
                if isinstance(rev, str): rev = json.loads(rev)
                if str(p.id) not in [str(x) for x in rev]:
                    asym.append((p.title, t.title))
        if not asym:
            ok("모든 배타 관계 양방향 대칭 보장")
        else:
            for a, b in asym[:3]: warn(f"비대칭: {a} → {b}")
            if len(asym) > 3: warn(f"... 외 {len(asym)-3}건 더")
            fail(f"비대칭 {len(asym)}건 (graph_builder가 런타임 보정하지만 DB 정리 권장)")
        results["exclusion"] = len(asym) == 0
    except Exception as e:
        fail(f"점검 실패: {e}"); results["exclusion"] = False

# ─────────────────────────────────────────────────────────────────
# 요약
# ─────────────────────────────────────────────────────────────────
section("최종 점검 요약")
labels = {"imports":"Import 전체","db":"DB 연결+데이터","window":"WINDOW 경계",
          "solvers":"솔버 교차검증","roadmap":"roadmap E2E","main":"main.py 라우터","exclusion":"배타 대칭성"}
for k, l in labels.items():
    print(f"  {'✅' if results.get(k) else '❌'}  {l}")
passed = sum(1 for v in results.values() if v)
print(f"\n  {'─'*60}\n  통과: {passed} / {len(results)}\n{'═'*W}\n")