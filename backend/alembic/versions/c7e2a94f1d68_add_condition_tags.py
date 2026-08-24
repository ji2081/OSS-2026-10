"""add condition_tags

policies.condition_tags — 미혼/장애/다문화 등 age/income_level/region/
is_employed 하드 필터로 못 거르는 자격조건을 고정 태그로 기록.
user_profiles.confirmed_tags — 사용자가 그 태그 질문에 답한 결과(예/아니오)를
저장해서, 한 번 답한 태그는 다시 안 물어보게 한다.
policies_etl_staging.condition_tags — ETL 결과도 같은 필드를 실어야 승격 시
그대로 넘어간다.

Revision ID: c7e2a94f1d68
Revises: a3f9c8d21b4e
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c7e2a94f1d68'
down_revision: Union[str, Sequence[str], None] = 'a3f9c8d21b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'policies',
        sa.Column('condition_tags', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        'user_profiles',
        sa.Column('confirmed_tags', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        'policies_etl_staging',
        sa.Column('condition_tags', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column('policies_etl_staging', 'condition_tags')
    op.drop_column('user_profiles', 'confirmed_tags')
    op.drop_column('policies', 'condition_tags')
