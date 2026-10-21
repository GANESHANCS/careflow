"""add_import_rollback_and_audit_provenance

Revision ID: f14a8b7d9e23
Revises: e63cafcc4f9d
Create Date: 2026-10-10 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f14a8b7d9e23'
down_revision: Union[str, Sequence[str], None] = 'e63cafcc4f9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add rollback metadata columns to import_jobs
    existing_job_cols = [c['name'] for c in inspector.get_columns('import_jobs')] if 'import_jobs' in existing_tables else []
    with op.batch_alter_table('import_jobs', schema=None) as batch_op:
        if 'rolled_back_at' not in existing_job_cols:
            batch_op.add_column(sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True))
        if 'rolled_back_by' not in existing_job_cols:
            batch_op.add_column(sa.Column('rolled_back_by', sa.String(length=100), nullable=True))
        if 'rollback_reason' not in existing_job_cols:
            batch_op.add_column(sa.Column('rollback_reason', sa.String(length=255), nullable=True))

    # 2. Add last_import_job_id column to observations
    existing_obs_cols = [c['name'] for c in inspector.get_columns('observations')] if 'observations' in existing_tables else []
    with op.batch_alter_table('observations', schema=None) as batch_op:
        if 'last_import_job_id' not in existing_obs_cols:
            batch_op.add_column(sa.Column('last_import_job_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_observations_last_import_job_id',
                'import_jobs',
                ['last_import_job_id'],
                ['id'],
                ondelete='SET NULL'
            )
            batch_op.create_index(op.f('ix_observations_last_import_job_id'), ['last_import_job_id'], unique=False)

    # 3. Create import_observation_records table for change-tracking and before-images
    if 'import_observation_records' not in existing_tables:
        op.create_table(
            'import_observation_records',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('import_job_id', sa.Integer(), nullable=False),
            sa.Column('observation_id', sa.String(length=128), nullable=False),
            sa.Column('action', sa.String(length=20), nullable=False),
            sa.Column('previous_value', sa.Float(), nullable=True),
            sa.Column('previous_value_type', sa.String(length=32), nullable=True),
            sa.Column('previous_validation_status', sa.String(length=32), nullable=True),
            sa.Column('previous_source_file', sa.String(length=255), nullable=True),
            sa.Column('previous_source_sheet', sa.String(length=128), nullable=True),
            sa.Column('previous_source_row', sa.Integer(), nullable=True),
            sa.Column('previous_ingested_at', sa.String(length=64), nullable=True),
            sa.Column('previous_transformation_version', sa.String(length=32), nullable=True),
            sa.Column('previous_import_job_id', sa.Integer(), nullable=True),
            sa.Column('new_value', sa.Float(), nullable=True),
            sa.Column('new_value_type', sa.String(length=32), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['import_job_id'], ['import_jobs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(
            op.f('ix_import_observation_records_id'), 'import_observation_records', ['id'], unique=False
        )
        op.create_index(
            op.f('ix_import_observation_records_import_job_id'), 'import_observation_records', ['import_job_id'], unique=False
        )
        op.create_index(
            op.f('ix_import_observation_records_observation_id'), 'import_observation_records', ['observation_id'], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Drop import_observation_records table
    if 'import_observation_records' in existing_tables:
        op.drop_index(op.f('ix_import_observation_records_observation_id'), table_name='import_observation_records')
        op.drop_index(op.f('ix_import_observation_records_import_job_id'), table_name='import_observation_records')
        op.drop_index(op.f('ix_import_observation_records_id'), table_name='import_observation_records')
        op.drop_table('import_observation_records')

    # 2. Drop last_import_job_id from observations
    existing_obs_cols = [c['name'] for c in inspector.get_columns('observations')] if 'observations' in existing_tables else []
    with op.batch_alter_table('observations', schema=None) as batch_op:
        if 'last_import_job_id' in existing_obs_cols:
            batch_op.drop_index(op.f('ix_observations_last_import_job_id'))
            batch_op.drop_constraint('fk_observations_last_import_job_id', type_='foreignkey')
            batch_op.drop_column('last_import_job_id')

    # 3. Drop rollback metadata from import_jobs
    existing_job_cols = [c['name'] for c in inspector.get_columns('import_jobs')] if 'import_jobs' in existing_tables else []
    with op.batch_alter_table('import_jobs', schema=None) as batch_op:
        if 'rollback_reason' in existing_job_cols:
            batch_op.drop_column('rollback_reason')
        if 'rolled_back_by' in existing_job_cols:
            batch_op.drop_column('rolled_back_by')
        if 'rolled_back_at' in existing_job_cols:
            batch_op.drop_column('rolled_back_at')
