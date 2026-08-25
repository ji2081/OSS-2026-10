"""
LLM이 뽑아낸 PolicySchema를 policies_etl_staging 테이블에 적재한다.

policies에 직접 upsert하지 않는 이유
-------------------------------------
기존 policies의 상당수는 팀원이 손으로 검증·보정한 데이터다(exclusive_with
UUID 양방향 보정 등). ETL을 재실행했을 때 같은 title의 정책을 다시 긁어와서
곧바로 policies를 덮어써 버리면, 그 손검증 데이터가 방금 돌린 LLM 결과로
조용히 사라질 위험이 있다. 그래서 이번 결과는 항상 policies_etl_staging에만
쌓고, title이 기존 policies와 겹치면 matched_existing_id에 표시해 둔다.
실제 policies/policy_tiers로의 승격은 etl/promote.py가 사람의 확인을 거쳐
수행한다 — 겹치지 않는(순수 신규) 항목은 안전하게 자동 승격하고, 겹치는
항목은 기존 값과 나란히 비교해서 사람이 판단한다.

exclusive_with는 정책명 그대로 저장해 둔다. UUID 매칭은 승격 시점에
(그때는 어떤 정책이 실제로 policies에 존재하는지 확정되므로) 수행한다.
"""
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field

import asyncpg

from etl.validate.schema import PolicySchema


@dataclass
class InsertResult:
    success: int = 0  # policies_etl_staging에 적재 성공한 수
    skipped: int = 0  # confidence 낮아서 건너뛴 수
    failed:  int = 0  # 검증/적재 실패한 수
    errors:  list[str] = field(default_factory=list)


FIND_POLICY_BY_TITLE_SQL = "SELECT id FROM policies WHERE title = $1 LIMIT 1"

# 같은 title로 이미 검토 대기 중인 staging 행이 있으면(=ETL을 여러 번 재실행)
# 새 행을 또 쌓지 않고 그 행을 최신 결과로 갱신한다. 안 그러면 재실행할
# 때마다 같은 정책이 staging에 계속 쌓이고, promote-new가 그걸 각각 별개로
# 승격시켜 policies에 진짜 중복 행을 만들어버린다(실제로 재현해서 확인한
# 버그). review_status가 'approved'/'rejected'로 이미 처리된 행은 과거
# 기록이니 건드리지 않고 새로 하나 더 쌓는다.
FIND_PENDING_STAGING_BY_TITLE_SQL = (
    "SELECT id FROM policies_etl_staging WHERE title = $1 AND review_status = 'pending' LIMIT 1"
)

UPDATE_STAGING_SQL = """
UPDATE policies_etl_staging SET
    etl_run_id = $2, fetched_at = $3,
    category = $4, benefit_type = $5, host_org = $6, source_url = $7,
    super_region = $8, age_min = $9, age_max = $10,
    income_standard = $11, income_threshold = $12, income_threshold_min = $13, parent_income_threshold = $14, income_type = $15,
    target_unemployed_only = $16, situational_condition = $17, benefit_description = $18,
    benefit_start_lag_days = $19, apply_start = $20, apply_end = $21, is_open_ended = $22,
    exclusive_with = $23::jsonb, exclusive_scope = $24, is_supplementary = $25, confidence = $26, tiers = $27::jsonb,
    condition_tags = $28::jsonb, matched_existing_id = $29
WHERE id = $1
"""

INSERT_STAGING_SQL = """
INSERT INTO policies_etl_staging (
    id, etl_run_id, fetched_at,
    title, category, benefit_type, host_org, source_url,
    super_region, age_min, age_max,
    income_standard, income_threshold, income_threshold_min, parent_income_threshold, income_type,
    target_unemployed_only, situational_condition, benefit_description,
    benefit_start_lag_days, apply_start, apply_end, is_open_ended,
    exclusive_with, exclusive_scope, is_supplementary, confidence, tiers,
    condition_tags, matched_existing_id, review_status
) VALUES (
    $1, $2, $3,
    $4, $5, $6, $7, $8,
    $9, $10, $11,
    $12, $13, $14, $15, $16,
    $17, $18, $19,
    $20, $21, $22, $23,
    $24::jsonb, $25, $26, $27, $28::jsonb,
    $29::jsonb, $30, 'pending'
)
"""

INSERT_LOG_SQL = """
INSERT INTO etl_logs (
    id, source, run_at, total_extracted, total_inserted,
    total_skipped, total_failed, errors
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
"""


def _normalize_title(title: str) -> str:
    return " ".join(title.split()).strip()


async def _find_matched_existing_id(conn: asyncpg.Connection, title: str) -> uuid.UUID | None:
    row = await conn.fetchrow(FIND_POLICY_BY_TITLE_SQL, title)
    return row["id"] if row else None


async def stage_policy(conn: asyncpg.Connection, schema: PolicySchema, etl_run_id: uuid.UUID) -> uuid.UUID:
    matched_id = await _find_matched_existing_id(conn, schema.title)
    tiers_json = json.dumps(
        [t.model_dump() for t in schema.tiers],
        ensure_ascii=False,
    )
    exclusive_json = json.dumps(schema.exclusive_with, ensure_ascii=False)
    condition_tags_json = json.dumps(schema.condition_tags, ensure_ascii=False)

    pending = await conn.fetchrow(FIND_PENDING_STAGING_BY_TITLE_SQL, schema.title)
    if pending is not None:
        staging_id = pending["id"]
        await conn.execute(
            UPDATE_STAGING_SQL,
            staging_id, etl_run_id, datetime.utcnow(),
            schema.category.value, schema.benefit_type.value, schema.host_org, schema.source_url,
            schema.super_region, schema.age_min, schema.age_max,
            schema.income_standard, schema.income_threshold, schema.income_threshold_min,
            schema.parent_income_threshold, schema.income_type.value,
            schema.target_unemployed_only, schema.situational_condition, schema.benefit_description,
            schema.benefit_start_lag_days, schema.apply_start, schema.apply_end, schema.is_open_ended,
            exclusive_json, schema.exclusive_scope, schema.is_supplementary, schema.confidence, tiers_json,
            condition_tags_json, matched_id,
        )
        return staging_id

    staging_id = uuid.uuid4()
    await conn.execute(
        INSERT_STAGING_SQL,
        staging_id, etl_run_id, datetime.utcnow(),
        schema.title, schema.category.value, schema.benefit_type.value, schema.host_org, schema.source_url,
        schema.super_region, schema.age_min, schema.age_max,
        schema.income_standard, schema.income_threshold, schema.income_threshold_min,
        schema.parent_income_threshold, schema.income_type.value,
        schema.target_unemployed_only, schema.situational_condition, schema.benefit_description,
        schema.benefit_start_lag_days, schema.apply_start, schema.apply_end, schema.is_open_ended,
        exclusive_json, schema.exclusive_scope, schema.is_supplementary, schema.confidence, tiers_json,
        condition_tags_json, matched_id,
    )
    return staging_id


async def insert_batch(
    dsn: str,
    schemas: list[PolicySchema | None],
    source: str = "etl",
) -> InsertResult:
    """policies_etl_staging에 적재만 한다 — 실제 policies 반영은 etl/promote.py 참고."""
    result = InsertResult()
    total_extracted = len(schemas)
    etl_run_id = uuid.uuid4()

    # PgBouncer 트랜잭션 모드 + asyncpg prepared statement 캐시 비호환 문제
    # (promote.py에서 DuplicatePreparedStatementError로 실제 재현됨) 대응.
    conn = await asyncpg.connect(dsn, ssl='require', statement_cache_size=0)
    try:
        matched_count = 0
        for schema in schemas:
            if schema is None or isinstance(schema, Exception):
                result.failed += 1
                continue

            if schema.confidence < 0.5:
                result.skipped += 1
                result.errors.append(f"[SKIP] confidence 낮음 ({schema.confidence:.2f}): {schema.title}")
                continue

            try:
                await stage_policy(conn, schema, etl_run_id)
                result.success += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(f"[ERROR] {schema.title}: {e}")

        await conn.execute(
            INSERT_LOG_SQL,
            etl_run_id, source, datetime.utcnow(),
            total_extracted, result.success, result.skipped, result.failed,
            json.dumps(result.errors, ensure_ascii=False),
        )
        print(f"  → etl_run_id: {etl_run_id}  (검토/승격은 python -m etl.promote --run {etl_run_id})")
    finally:
        await conn.close()

    return result
