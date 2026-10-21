"""add_phase_9b_import_batches

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-10-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add Phase 9B ImportBatches table and batch_id relation."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create import_batches table if not already present
    if 'import_batches' not in existing_tables:
        op.create_table(
            'import_batches',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('batch_code', sa.String(length=64), nullable=False),
            sa.Column('source', sa.String(length=64), server_default='DIRECTORY_WATCHER', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='QUEUED', nullable=False),
            sa.Column('total_files', sa.Integer(), server_default='0', nullable=False),
            sa.Column('processed_files', sa.Integer(), server_default='0', nullable=False),
            sa.Column('successful_files', sa.Integer(), server_default='0', nullable=False),
            sa.Column('failed_files', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_records', sa.Integer(), server_default='0', nullable=False),
            sa.Column('imported_records', sa.Integer(), server_default='0', nullable=False),
            sa.Column('rejected_records', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('initiated_by', sa.String(length=100), nullable=True),
            sa.Column('error_summary', sa.String(length=512), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_import_batches_id', 'import_batches', ['id'], unique=False)
        op.create_index('ix_import_batches_batch_code', 'import_batches', ['batch_code'], unique=True)
        op.create_index('ix_import_batches_status', 'import_batches', ['status'], unique=False)
        op.create_index('ix_import_batches_created_at', 'import_batches', ['created_at'], unique=False)

    # 2. Add batch_id to import_jobs table
    if 'import_jobs' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('import_jobs')]
        with op.batch_alter_table('import_jobs', schema=None) as batch_op:
            if 'batch_id' not in existing_cols:
                batch_op.add_column(sa.Column('batch_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    'fk_import_jobs_batch_id',
                    'import_batches',
                    ['batch_id'],
                    ['id'],
                    ondelete='SET NULL'
                )
                batch_op.create_index('ix_import_jobs_batch_id', ['batch_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema to reverse Phase 9B additions."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'import_jobs' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('import_jobs')]
        with op.batch_alter_table('import_jobs', schema=None) as batch_op:
            if 'batch_id' in existing_cols:
                try:
                    batch_op.drop_index('ix_import_jobs_batch_id')
                except Exception:
                    pass
                try:
                    batch_op.drop_constraint('fk_import_jobs_batch_id', type_='foreignkey')
                except Exception:
                    pass
                batch_op.drop_column('batch_id')

    if 'import_batches' in existing_tables:
        try:
            op.drop_index('ix_import_batches_created_at', table_name='import_batches')
            op.drop_index('ix_import_batches_status', table_name='import_batches')
            op.drop_index('ix_import_batches_batch_code', table_name='import_batches')
            op.drop_index('ix_import_batches_id', table_name='import_batches')
        except Exception:
            pass
        op.drop_table('import_batches')
