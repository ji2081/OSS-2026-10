import json
from datetime import datetime, timezone
from dataclasses import dataclass, field

import asyncpg

from etl.validate.schema import PolicySchema


@dataclass
class InsertResult:
    success: int = 0
    skipped: int = 0
    failed:  int = 0
    errors:  list[str] = field(default_factory=list)


UPSERT_POLICY_SQL = """
INSERT INTO policies (
    title, category, benefit_type, host_org,
    super_region, sub_region,
    age_min, age_max, income_standard, income_limit,
    total_benefit, benefit_duration_months, benefit_description,
    apply_start, apply_end, is_active,
    exclusive_with, source_url, confidence, raw_data,
    updated_at
)
VALUES (
    $1, $2, $3, $4,
    $5, $6,
    $7, $8, $9, $10,
    $11, $12, $13,
    $14, $15, $16,
    $17::jsonb, $18, $19, $20, $21
    NOW()
)
ON CONFLICT (title) DO UPDATE SET
    category                = EXCLUDED.category,
    benefit_type            = EXCLUDED.benefit_type,
    host_org                = EXCLUDED.host_org,
    super_region            = EXCLUDED.super_region,
    sub_region              = EXCLUDED.sub_region,
    age_min                 = EXCLUDED.age_min,
    age_max                 = EXCLUDED.age_max,
    income_standard         = EXCLUDED.income_standard,
    income_limit            = EXCLUDED.income_limit,
    total_benefit           = EXCLUDED.total_benefit,
    benefit_duration_months = EXCLUDED.benefit_duration_months,
    benefit_description     = EXCLUDED.benefit_description,
    apply_start             = EXCLUDED.apply_start,
    apply_end               = EXCLUDED.apply_end,
    is_active               = EXCLUDED.is_active,
    exclusive_with          = EXCLUDED.exclusive_with,
    source_url              = EXCLUDED.source_url,
    confidence              = EXCLUDED.confidence,
    raw_data                = EXCLUDED.raw_data,
    updated_at              = NOW()
    target_unemployed_only = EXCLUDED.target_unemployed_only,
RETURNING id
"""

INSERT_LOG_SQL = """
INSERT INTO etl_logs (
    run_at, source, total_extracted, total_inserted,
    total_skipped, total_failed, errors
)
VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
"""


async def insert_policy(conn: asyncpg.Connection, schema: PolicySchema) -> bool:
    row = await conn.fetchrow(
        UPSERT_POLICY_SQL,
        schema.title,
        schema.category.value,
        schema.benefit_type.value,
        schema.host_org,
        schema.super_region,
        schema.sub_region,
        schema.age_min,
        schema.age_max,
        schema.income_standard,
        schema.income_limit,
        schema.total_benefit,
        schema.benefit_duration_months,
        schema.benefit_description,
        schema.apply_start,
        schema.apply_end,
        schema.is_active,
        json.dumps(schema.exclusive_with, ensure_ascii=False),
        schema.source_url,
        schema.confidence,
        schema.raw_data,
        schema.target_unemployed_only,
    )
    return row is not None


async def insert_batch(
    dsn: str,
    schemas: list[PolicySchema | None],
    source: str = "etl",
) -> InsertResult:
    result = InsertResult()
    total_extracted = len(schemas)

    conn = await asyncpg.connect(dsn)
    try:
        for schema in schemas:
            if schema is None or isinstance(schema, Exception):
                result.failed += 1
                continue

            if schema.confidence < 0.5:
                result.skipped += 1
                result.errors.append(f"[SKIP] confidence 낮음 ({schema.confidence:.2f}): {schema.title}")
                continue

            try:
                await insert_policy(conn, schema)
                result.success += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(f"[ERROR] {schema.title}: {e}")

        await conn.execute(
            INSERT_LOG_SQL,
            datetime.now(timezone.utc),
            source,
            total_extracted,
            result.success,
            result.skipped,
            result.failed,
            json.dumps(result.errors, ensure_ascii=False),
        )
    finally:
        await conn.close()

    return result