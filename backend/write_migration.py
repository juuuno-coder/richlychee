"""Write migration file for Phase 6-8 tables."""

migration_content = '''"""Create Phase 6-8 tables: presets, schedules, price monitoring

Revision ID: 7392895cd065
Revises: 13dcf54eec81
Create Date: 2026-02-13 16:20:39.675890
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7392895cd065'
down_revision: Union[str, None] = '13dcf54eec81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crawl_presets table
    op.create_table(
        'crawl_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('site_url', sa.String(length=255), nullable=False),
        sa.Column('url_pattern', sa.String(length=255), nullable=False),
        sa.Column('crawler_type', sa.String(length=20), nullable=False),
        sa.Column('crawl_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create crawl_schedules table
    op.create_table(
        'crawl_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('target_url', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('crawl_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('total_runs', sa.Integer(), default=0),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create price_histories table
    op.create_table(
        'price_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crawled_product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crawled_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), default='KRW'),
        sa.Column('original_price', sa.Integer(), nullable=True),
        sa.Column('price_change', sa.Integer(), nullable=True),
        sa.Column('price_change_percent', sa.Float(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create price_alerts table
    op.create_table(
        'price_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('crawled_product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crawled_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(length=20), nullable=False),
        sa.Column('target_price', sa.Integer(), nullable=True),
        sa.Column('change_threshold', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('price_alerts')
    op.drop_table('price_histories')
    op.drop_table('crawl_schedules')
    op.drop_table('crawl_presets')
'''

with open('/app/alembic/versions/7392895cd065_create_phase_6_8_tables_presets_.py', 'w') as f:
    f.write(migration_content)

print("Migration file written successfully!")
