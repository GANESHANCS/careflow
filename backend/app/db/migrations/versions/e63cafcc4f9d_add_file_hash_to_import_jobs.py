"""add_file_hash_to_import_jobs

Revision ID: e63cafcc4f9d
Revises: 56a26ed15259
Create Date: 2026-10-03 16:24:13.399973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e63cafcc4f9d'
down_revision: Union[str, Sequence[str], None] = '56a26ed15259'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('import_jobs', sa.Column('file_hash', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_import_jobs_file_hash'), 'import_jobs', ['file_hash'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_import_jobs_file_hash'), table_name='import_jobs')
    with op.batch_alter_table('import_jobs', schema=None) as batch_op:
        batch_op.drop_column('file_hash')
