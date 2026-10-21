"""add_phase_11b_district_observations

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-10-21 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add Phase 11B DistrictObservation table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create district_observations table if not already present
    if 'district_observations' not in existing_tables:
        op.create_table(
            'district_observations',
            sa.Column('id', sa.String(length=160), nullable=False),
            sa.Column('state', sa.String(length=128), nullable=False),
            sa.Column('district', sa.String(length=128), nullable=False),
            sa.Column('s_no', sa.String(length=32), nullable=False),
            sa.Column('parameter_name', sa.String(length=512), nullable=False),
            sa.Column('subgroup_type', sa.String(length=64), server_default='TOTAL', nullable=False),
            sa.Column('is_subgroup_total', sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column('indicator_id', sa.String(length=64), nullable=True),
            sa.Column('financial_year', sa.String(length=16), nullable=False),
            sa.Column('reporting_month', sa.String(length=7), nullable=False),
            sa.Column('observation_date', sa.String(length=10), nullable=False),
            sa.Column('value', sa.Float(), nullable=True),
            sa.Column('value_type', sa.String(length=32), server_default='VALID', nullable=False),
            sa.Column('validation_status', sa.String(length=32), server_default='VALIDATED', nullable=False),
            sa.Column('reported_annual_total', sa.Float(), nullable=True),
            sa.Column('source_file', sa.String(length=255), nullable=False),
            sa.Column('source_row', sa.Integer(), nullable=True),
            sa.Column('ingested_at', sa.String(length=64), nullable=False),
            sa.Column('transformation_version', sa.String(length=32), server_default='1.0.0', nullable=False),
            sa.Column('last_import_job_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['last_import_job_id'], ['import_jobs.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('district', 's_no', 'subgroup_type', 'reporting_month', name='uq_district_obs_natural_key')
        )
        op.create_index('ix_district_observations_state', 'district_observations', ['state'], unique=False)
        op.create_index('ix_district_observations_district', 'district_observations', ['district'], unique=False)
        op.create_index('ix_district_observations_s_no', 'district_observations', ['s_no'], unique=False)
        op.create_index('ix_district_observations_subgroup_type', 'district_observations', ['subgroup_type'], unique=False)
        op.create_index('ix_district_observations_is_subgroup_total', 'district_observations', ['is_subgroup_total'], unique=False)
        op.create_index('ix_district_observations_reporting_month', 'district_observations', ['reporting_month'], unique=False)
        op.create_index('ix_district_observations_observation_date', 'district_observations', ['observation_date'], unique=False)
        op.create_index('ix_district_observations_indicator_id', 'district_observations', ['indicator_id'], unique=False)
        op.create_index('ix_district_observations_last_import_job_id', 'district_observations', ['last_import_job_id'], unique=False)
        op.create_index('idx_dist_obs_natural_key', 'district_observations', ['district', 's_no', 'subgroup_type', 'reporting_month'], unique=False)
        op.create_index('idx_dist_obs_query', 'district_observations', ['district', 's_no', 'reporting_month'], unique=False)
        op.create_index('idx_dist_obs_state_district', 'district_observations', ['state', 'district'], unique=False)


def downgrade() -> None:
    """Downgrade schema to reverse Phase 11B additions."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'district_observations' in existing_tables:
        indexes = [
            'idx_dist_obs_state_district',
            'idx_dist_obs_query',
            'idx_dist_obs_natural_key',
            'ix_district_observations_last_import_job_id',
            'ix_district_observations_indicator_id',
            'ix_district_observations_observation_date',
            'ix_district_observations_reporting_month',
            'ix_district_observations_is_subgroup_total',
            'ix_district_observations_subgroup_type',
            'ix_district_observations_s_no',
            'ix_district_observations_district',
            'ix_district_observations_state'
        ]
        for idx in indexes:
            try:
                op.drop_index(idx, table_name='district_observations')
            except Exception:
                pass
        op.drop_table('district_observations')
