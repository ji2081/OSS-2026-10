"""
etl/promote.py — policies_etl_staging에 쌓인 결과를 실제 policies/policy_tiers로
승격시키는 검토 도구.

     python -m etl.promote list [--run <etl_run_id>]
     python -m etl.promote promote-new [--run <etl_run_id>]
     python -m etl.promote diff <staging_id>
     python -m etl.promote approve <staging_id>
     python -m etl.promote reject <staging_id>

"신규"(matched_existing_id가 없는, 기존 정책명과 안 겹치는 항목)는 손검증
데이터를 건드릴 위험이 없으므로 promote-new로 한 번에 승격 가능하다.
"충돌"(matched_existing_id가 있는, 기존 정책명과 겹치는 항목)은 diff로
기존 값과 나란히 비교해본 뒤 approve로 명시적으로 승인해야만 승격된다 —
아무 것도 자동으로 덮어쓰지 않는다.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
load_dotenv()  # backend/ 밖에서 실행하는 경우 대비

DB_DSN: str = os.environ.get(
    "DB_DSN",
    "postgresql://policy_admin:password@localhost:5432/youth_policy",
)

STAGING_FIELDS = [
    "title", "category", "benefit_type", "host_org", "source_url",
    "super_region", "age_min", "age_max",
    "income_standard", "income_threshold", "income_threshold_min", "parent_income_threshold", "income_type",
    "target_unemployed_only", "situational_condition", "benefit_description",
    "benefit_start_lag_days", "apply_start", "apply_end", "is_open_ended",
    "exclusive_scope", "is_supplementary", "confidence", "condition_tags",
]
# tiers는 policies에선 관계형 policy_tiers, staging에선 JSONB라 표현 형태가
# 아예 다르므로 위 목록에서 빼고 cmd_diff 하단에서 따로 비교한다.
# exclusive_with도 policies는 UUID 배열, staging은 정책명 배열이라 문자열
# 비교가 의미 없어서 뺐다 — 승격 시점에 이름→UUID로 다시 계산된다.


def _normalize_title(title: str) -> str:
    return " ".join(title.split()).strip()


async def _connect() -> asyncpg.Connection:
    # Supabase는 모든 연결을 PgBouncer 트랜잭션 모드로 라우팅하는데, 이 모드는
    # asyncpg의 client-side prepared statement 캐시와 호환되지 않는다
    # (DuplicatePreparedStatementError로 실제 재현됨). backend/database.py가
    # 이미 겪은 문제와 같은 것 — statement_cache_size=0으로 캐시를 꺼야 한다.
    return await asyncpg.connect(DB_DSN, ssl='require', statement_cache_size=0)


async def cmd_list(run_id: str | None) -> None:
    conn = await _connect()
    try:
        if run_id:
            rows = await conn.fetch(
                "SELECT id, title, matched_existing_id, confidence, review_status "
                "FROM policies_etl_staging WHERE etl_run_id = $1 ORDER BY title",
                uuid.UUID(run_id),
            )
        else:
            rows = await conn.fetch(
                "SELECT id, title, matched_existing_id, confidence, review_status "
                "FROM policies_etl_staging WHERE review_status = 'pending' ORDER BY title",
            )

        new_rows = [r for r in rows if r["matched_existing_id"] is None]
        conflict_rows = [r for r in rows if r["matched_existing_id"] is not None]

        print(f"\n신규 (자동 승격 가능, {len(new_rows)}건)")
        for r in new_rows:
            print(f"  [{r['id']}] {r['title']}  (confidence={r['confidence']:.2f})")

        print(f"\n충돌 (기존 정책명과 겹침 — diff 확인 후 approve 필요, {len(conflict_rows)}건)")
        for r in conflict_rows:
            print(f"  [{r['id']}] {r['title']}  → 기존 정책 {r['matched_existing_id']}  (confidence={r['confidence']:.2f})")
    finally:
        await conn.close()


async def _resolve_exclusive_with(conn: asyncpg.Connection, pending: list[tuple[uuid.UUID, list[str]]]) -> list[str]:
    rows = await conn.fetch("SELECT id, title FROM policies WHERE is_active = true")
    title_to_id = {_normalize_title(r["title"]).casefold(): r["id"] for r in rows}

    warnings: list[str] = []
    for policy_id, raw_names in pending:
        resolved: list[str] = []
        for name in raw_names:
            target_id = title_to_id.get(_normalize_title(name).casefold())
            if target_id is None:
                warnings.append(f"[EXCLUSIVE 미매칭] {name!r} (정책 {policy_id})")
                continue
            if target_id != policy_id:
                resolved.append(str(target_id))
        await conn.execute(
            "UPDATE policies SET exclusive_with = $1::jsonb WHERE id = $2",
            json.dumps(resolved, ensure_ascii=False), policy_id,
        )
    return warnings


async def _promote_row(conn: asyncpg.Connection, row: asyncpg.Record) -> uuid.UUID:
    """staging row 하나를 policies(+policy_tiers)로 반영. 기존에 매칭되는
    정책이 있으면 그 id를 그대로 UPDATE, 없으면 새 id로 INSERT."""
    existing_id = row["matched_existing_id"]
    now = datetime.utcnow()
    policy_id = existing_id or uuid.uuid4()

    if existing_id is not None:
        await conn.execute(
            """
            UPDATE policies SET
                category=$2, benefit_type=$3, host_org=$4, source_url=$5, super_region=$6,
                age_min=$7, age_max=$8, income_standard=$9, income_threshold=$10,
                income_threshold_min=$11, parent_income_threshold=$12, income_type=$13,
                target_unemployed_only=$14, situational_condition=$15, benefit_description=$16,
                benefit_start_lag_days=$17, apply_start=$18, apply_end=$19, is_open_ended=$20,
                exclusive_scope=$21, is_supplementary=$22, confidence=$23, condition_tags=$24::jsonb,
                updated_at=$25
            WHERE id=$1
            """,
            policy_id, row["category"], row["benefit_type"], row["host_org"], row["source_url"], row["super_region"],
            row["age_min"], row["age_max"], row["income_standard"], row["income_threshold"],
            row["income_threshold_min"], row["parent_income_threshold"], row["income_type"],
            row["target_unemployed_only"], row["situational_condition"], row["benefit_description"],
            row["benefit_start_lag_days"], row["apply_start"], row["apply_end"], row["is_open_ended"],
            row["exclusive_scope"], row["is_supplementary"], row["confidence"], row["condition_tags"], now,
        )
    else:
        await conn.execute(
            """
            INSERT INTO policies (
                id, title, category, benefit_type, host_org, source_url, super_region,
                age_min, age_max, income_standard, income_threshold, income_threshold_min,
                parent_income_threshold, income_type, target_unemployed_only, situational_condition,
                benefit_description, benefit_start_lag_days, apply_start, apply_end, is_open_ended,
                exclusive_with, exclusive_scope, is_supplementary, condition_tags, is_active, confidence, updated_at
            ) VALUES (
                $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
                $17,$18,$19,$20,$21,$22::jsonb,$23,$24,$25::jsonb,true,$26,$27
            )
            """,
            policy_id, row["title"], row["category"], row["benefit_type"], row["host_org"], row["source_url"],
            row["super_region"], row["age_min"], row["age_max"], row["income_standard"], row["income_threshold"],
            row["income_threshold_min"], row["parent_income_threshold"], row["income_type"],
            row["target_unemployed_only"], row["situational_condition"], row["benefit_description"],
            row["benefit_start_lag_days"], row["apply_start"], row["apply_end"], row["is_open_ended"],
            "[]", row["exclusive_scope"], row["is_supplementary"], row["condition_tags"], row["confidence"], now,
        )

    await conn.execute("DELETE FROM policy_tiers WHERE policy_id = $1", policy_id)
    tiers = json.loads(row["tiers"]) if isinstance(row["tiers"], str) else row["tiers"]
    for t in tiers:
        await conn.execute(
            "INSERT INTO policy_tiers (id, policy_id, max_income_ratio, monthly_benefit, duration_months) "
            "VALUES ($1,$2,$3,$4,$5)",
            uuid.uuid4(), policy_id, t.get("max_income_ratio"), t["monthly_benefit"], t["duration_months"],
        )

    await conn.execute(
        "UPDATE policies_etl_staging SET review_status='approved', reviewed_at=$2, promoted_policy_id=$3 WHERE id=$1",
        row["id"], now, policy_id,
    )
    return policy_id


async def cmd_promote_new(run_id: str | None) -> None:
    conn = await _connect()
    try:
        if run_id:
            rows = await conn.fetch(
                "SELECT * FROM policies_etl_staging WHERE etl_run_id = $1 "
                "AND matched_existing_id IS NULL AND review_status = 'pending'",
                uuid.UUID(run_id),
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM policies_etl_staging WHERE matched_existing_id IS NULL AND review_status = 'pending'"
            )

        pending_exclusive: list[tuple[uuid.UUID, list[str]]] = []
        for row in rows:
            policy_id = await _promote_row(conn, row)
            names = json.loads(row["exclusive_with"]) if isinstance(row["exclusive_with"], str) else row["exclusive_with"]
            if names:
                pending_exclusive.append((policy_id, names))

        warnings = await _resolve_exclusive_with(conn, pending_exclusive) if pending_exclusive else []

        print(f"승격 완료: {len(rows)}건")
        for w in warnings:
            print(f"  ⚠ {w}")
    finally:
        await conn.close()


async def cmd_diff(staging_id: str) -> None:
    conn = await _connect()
    try:
        staged = await conn.fetchrow("SELECT * FROM policies_etl_staging WHERE id = $1", uuid.UUID(staging_id))
        if staged is None:
            print("해당 staging id를 찾을 수 없습니다."); return
        if staged["matched_existing_id"] is None:
            print("이 항목은 기존 정책과 안 겹칩니다 — promote-new로 승격하세요."); return

        existing = await conn.fetchrow("SELECT * FROM policies WHERE id = $1", staged["matched_existing_id"])
        existing_tiers = await conn.fetch(
            "SELECT max_income_ratio, monthly_benefit, duration_months FROM policy_tiers WHERE policy_id = $1",
            staged["matched_existing_id"],
        )

        print(f"\n=== {staged['title']} ===")
        print(f"{'필드':<28} {'기존(policies)':<40} {'ETL 결과(staging)'}")
        for f in STAGING_FIELDS:
            old_v = existing[f] if f in existing.keys() else "(필드 없음)"
            new_v = staged[f]
            marker = "  ←달라짐" if str(old_v) != str(new_v) else ""
            print(f"{f:<28} {str(old_v)[:38]:<40} {str(new_v)[:60]}{marker}")

        print(f"\n{'tiers(기존)':<28} {[dict(t) for t in existing_tiers]}")
        print(f"{'tiers(ETL)':<28} {staged['tiers']}")
        print(f"\n승인하려면: python -m etl.promote approve {staging_id}")
        print(f"거절하려면: python -m etl.promote reject {staging_id}")
    finally:
        await conn.close()


async def cmd_approve(staging_id: str) -> None:
    conn = await _connect()
    try:
        row = await conn.fetchrow("SELECT * FROM policies_etl_staging WHERE id = $1", uuid.UUID(staging_id))
        if row is None:
            print("해당 staging id를 찾을 수 없습니다."); return
        policy_id = await _promote_row(conn, row)
        names = json.loads(row["exclusive_with"]) if isinstance(row["exclusive_with"], str) else row["exclusive_with"]
        if names:
            warnings = await _resolve_exclusive_with(conn, [(policy_id, names)])
            for w in warnings:
                print(f"  ⚠ {w}")
        print(f"승격 완료 → policies.id = {policy_id}")
    finally:
        await conn.close()


async def cmd_reject(staging_id: str) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "UPDATE policies_etl_staging SET review_status='rejected', reviewed_at=$2 WHERE id=$1",
            uuid.UUID(staging_id), datetime.utcnow(),
        )
        print("거절 처리됨 (policies는 변경되지 않음).")
    finally:
        await conn.close()


def _get_arg(flag: str) -> str | None:
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__); return

    cmd = sys.argv[1]
    if cmd == "list":
        asyncio.run(cmd_list(_get_arg("--run")))
    elif cmd == "promote-new":
        asyncio.run(cmd_promote_new(_get_arg("--run")))
    elif cmd == "diff":
        asyncio.run(cmd_diff(sys.argv[2]))
    elif cmd == "approve":
        asyncio.run(cmd_approve(sys.argv[2]))
    elif cmd == "reject":
        asyncio.run(cmd_reject(sys.argv[2]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
