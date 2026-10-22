"""add_phase_15_anomaly_review_workflow

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-10-22 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add Phase 15 anomaly review and immutable audit action tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create district_anomaly_reviews table if not present
    if 'district_anomaly_reviews' not in existing_tables:
        op.create_table(
            'district_anomaly_reviews',
            sa.Column('id', sa.String(length=160), nullable=False),
            sa.Column('signal_id', sa.String(length=160), nullable=False),
            sa.Column('district', sa.String(length=128), nullable=False),
            sa.Column('indicator_id', sa.String(length=64), nullable=False),
            sa.Column('reporting_month', sa.String(length=7), nullable=False),
            sa.Column('signal_type', sa.String(length=64), nullable=False),
            sa.Column('severity', sa.String(length=32), server_default='WARNING', nullable=False),
            sa.Column('current_status', sa.String(length=32), server_default='OPEN', nullable=False),
            sa.Column('trigger_reason', sa.String(length=512), nullable=False),
            sa.Column('metric_value', sa.Float(), nullable=True),
            sa.Column('expected_range', sa.String(length=128), nullable=True),
            sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
            sa.Column('last_reviewed_by_user_id', sa.Integer(), nullable=True),
            sa.Column('last_reviewed_by_username', sa.String(length=100), nullable=True),
            sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolution_reason', sa.String(length=512), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['last_reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('signal_id', name='uq_district_anomaly_review_signal_id')
        )
        op.create_index('ix_district_anomaly_reviews_signal_id', 'district_anomaly_reviews', ['signal_id'], unique=True)
        op.create_index('ix_district_anomaly_reviews_district', 'district_anomaly_reviews', ['district'], unique=False)
        op.create_index('ix_district_anomaly_reviews_indicator_id', 'district_anomaly_reviews', ['indicator_id'], unique=False)
        op.create_index('ix_district_anomaly_reviews_reporting_month', 'district_anomaly_reviews', ['reporting_month'], unique=False)
        op.create_index('ix_district_anomaly_reviews_current_status', 'district_anomaly_reviews', ['current_status'], unique=False)
        op.create_index('idx_anom_review_dist_month', 'district_anomaly_reviews', ['district', 'reporting_month'], unique=False)

    # 2. Create district_anomaly_review_actions table if not present
    if 'district_anomaly_review_actions' not in existing_tables:
        op.create_table(
            'district_anomaly_review_actions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('review_id', sa.String(length=160), nullable=False),
            sa.Column('action', sa.String(length=32), nullable=False),
            sa.Column('from_status', sa.String(length=32), nullable=False),
            sa.Column('to_status', sa.String(length=32), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['review_id'], ['district_anomaly_reviews.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
        )
        op.create_index('ix_district_anomaly_review_actions_review_id', 'district_anomaly_review_actions', ['review_id'], unique=False)
        op.create_index('idx_anom_action_created_at', 'district_anomaly_review_actions', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove Phase 15 anomaly review tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'district_anomaly_review_actions' in existing_tables:
        op.drop_table('district_anomaly_review_actions')

    if 'district_anomaly_reviews' in existing_tables:
        op.drop_table('district_anomaly_reviews')
