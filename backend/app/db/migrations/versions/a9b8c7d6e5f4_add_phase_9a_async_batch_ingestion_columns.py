"""add_phase_9a_async_batch_ingestion_columns

Revision ID: a9b8c7d6e5f4
Revises: f14a8b7d9e23
Create Date: 2026-10-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, Sequence[str], None] = 'f14a8b7d9e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add Phase 9A async batch ingestion tracking columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'import_jobs' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('import_jobs')]
        with op.batch_alter_table('import_jobs', schema=None) as batch_op:
            if 'processed_records' not in existing_cols:
                batch_op.add_column(sa.Column('processed_records', sa.Integer(), nullable=False, server_default='0'))
            if 'claimed_at' not in existing_cols:
                batch_op.add_column(sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True))
            if 'claimed_by' not in existing_cols:
                batch_op.add_column(sa.Column('claimed_by', sa.String(length=100), nullable=True))
            if 'heartbeat_at' not in existing_cols:
                batch_op.add_column(sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True))
            if 'retry_count' not in existing_cols:
                batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
            if 'max_retries' not in existing_cols:
                batch_op.add_column(sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'))
            if 'error_summary' not in existing_cols:
                batch_op.add_column(sa.Column('error_summary', sa.String(length=512), nullable=True))
            if 'schema_profile' not in existing_cols:
                batch_op.add_column(sa.Column('schema_profile', sa.String(length=64), nullable=True, server_default='mohfw_standard_v2'))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'import_jobs' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('import_jobs')]
        with op.batch_alter_table('import_jobs', schema=None) as batch_op:
            if 'schema_profile' in existing_cols:
                batch_op.drop_column('schema_profile')
            if 'error_summary' in existing_cols:
                batch_op.drop_column('error_summary')
            if 'max_retries' in existing_cols:
                batch_op.drop_column('max_retries')
            if 'retry_count' in existing_cols:
                batch_op.drop_column('retry_count')
            if 'heartbeat_at' in existing_cols:
                batch_op.drop_column('heartbeat_at')
            if 'claimed_by' in existing_cols:
                batch_op.drop_column('claimed_by')
            if 'claimed_at' in existing_cols:
                batch_op.drop_column('claimed_at')
            if 'processed_records' in existing_cols:
                batch_op.drop_column('processed_records')
