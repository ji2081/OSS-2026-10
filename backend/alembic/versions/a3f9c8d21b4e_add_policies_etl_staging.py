"""add policies_etl_staging

ETL이 뽑아낸 정책을 policies 테이블에 바로 upsert하지 않고 일단 여기 쌓아둔다.
같은 title이 이미 policies에 있으면(=손으로 검증했을 가능성이 있는 기존 정책과
충돌) matched_existing_id에 그 id를 채워서 "이건 검토 후 승격하라"는 표시를
남기고, 겹치지 않는 새 정책은 review_status='pending' 상태로 쌓였다가
etl/promote.py가 안전하게 골라서 policies/policy_tiers로 승격시킨다.

Revision ID: a3f9c8d21b4e
Revises: 71e3d6be0f26
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a3f9c8d21b4e'
down_revision: Union[str, Sequence[str], None] = '71e3d6be0f26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'policies_etl_staging',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # 이 행을 만든 ETL 실행 단위. etl_logs.id를 그대로 참조해서
        # "이 배치가 뭘 만들었는지" 나중에 추적할 수 있게 한다.
        sa.Column('etl_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        # PolicySchema와 동일한 필드
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('category', sa.String()),
        sa.Column('benefit_type', sa.String()),
        sa.Column('host_org', sa.String()),
        sa.Column('source_url', sa.String()),
        sa.Column('super_region', sa.String()),
        sa.Column('age_min', sa.Integer()),
        sa.Column('age_max', sa.Integer()),
        sa.Column('income_standard', sa.Text()),
        sa.Column('income_threshold', sa.Float()),
        sa.Column('income_threshold_min', sa.Float()),
        sa.Column('parent_income_threshold', sa.Float()),
        sa.Column('income_type', sa.String()),
        sa.Column('target_unemployed_only', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('situational_condition', sa.Text()),
        sa.Column('benefit_description', sa.Text()),
        sa.Column('benefit_start_lag_days', sa.Integer(), server_default=sa.text('0')),
        sa.Column('apply_start', sa.Date()),
        sa.Column('apply_end', sa.Date()),
        sa.Column('is_open_ended', sa.Boolean(), server_default=sa.text('false')),
        # 정책명 그대로 저장(승격 시점에 policies 테이블 기준으로 UUID 매칭).
        sa.Column('exclusive_with', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb")),
        sa.Column('exclusive_scope', sa.String(), server_default=sa.text("'lifetime'")),
        sa.Column('is_supplementary', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('confidence', sa.Float(), server_default=sa.text('1.0')),
        # [{"max_income_ratio":..,"monthly_benefit":..,"duration_months":..}, ...]
        # 승격 전까지는 검토용으로만 쓰이므로 policy_tiers처럼 별도 테이블을
        # 두지 않고 JSONB 하나로 가볍게 둔다.
        sa.Column('tiers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # 검토 워크플로우
        sa.Column('matched_existing_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('policies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_status', sa.String(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('promoted_policy_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('policies.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_policies_etl_staging_review_status', 'policies_etl_staging', ['review_status'])
    op.create_index('ix_policies_etl_staging_title', 'policies_etl_staging', ['title'])
    op.create_index('ix_policies_etl_staging_etl_run_id', 'policies_etl_staging', ['etl_run_id'])


def downgrade() -> None:
    op.drop_index('ix_policies_etl_staging_etl_run_id', table_name='policies_etl_staging')
    op.drop_index('ix_policies_etl_staging_title', table_name='policies_etl_staging')
    op.drop_index('ix_policies_etl_staging_review_status', table_name='policies_etl_staging')
    op.drop_table('policies_etl_staging')
