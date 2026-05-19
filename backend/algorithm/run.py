import sys, os, asyncio, time, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

import asyncpg
from stage_b_dp_dfs import solve_mwis_dp_dfs


async def load_policies() -> list:
    conn = await asyncpg.connect(os.getenv("DB_DSN"), statement_cache_size=0)
    rows = await conn.fetch("""
        SELECT title, total_benefit, exclusive_with
        FROM policies
        WHERE is_active = true
        AND benefit_type != 'loan'
        AND total_benefit IS NOT NULL
        AND total_benefit > 0
    """)
    await conn.close()
    result = []
    for r in rows:
        d = dict(r)
        exc = d["exclusive_with"]
        if isinstance(exc, str):
            d["exclusive_with"] = json.loads(exc)
        elif exc is None:
            d["exclusive_with"] = []
        result.append(d)
    return result


async def main():
    policies = await load_policies()

    has_exclusive = [p for p in policies if p["exclusive_with"]]
    print(f"전체 정책 수: {len(policies)}개")
    print(f"배타 관계 있는 정책: {len(has_exclusive)}개")
    for p in has_exclusive:
        print(f"  - {p['title']}: {p['exclusive_with']}")

    start = time.perf_counter()
    result, total = solve_mwis_dp_dfs(policies)
    elapsed = time.perf_counter() - start

    print("\n✅ 최적 조합:")
    for p in result:
        print(f"  - {p['title']}: {p['total_benefit']:,}원")
    print(f"\n💰 총 수혜액: {total:,}원 ({total//10000:,}만원)")
    print(f"⏱  실행 시간: {elapsed:.4f}초")


asyncio.run(main())