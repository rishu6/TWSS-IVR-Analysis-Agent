"""Effective-dated internal department attribution."""
from alembic import op
import sqlalchemy as sa

revision='0003'
down_revision='0002'


def upgrade():
    op.create_table('department_mappings',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('source_type',sa.String(20),nullable=False),sa.Column('source_value',sa.String(120),nullable=False),
        sa.Column('department',sa.String(120),nullable=False),sa.Column('effective_from',sa.DateTime(timezone=True),nullable=False),
        sa.Column('effective_to',sa.DateTime(timezone=True)))
    op.create_index('ix_department_mappings_source_value','department_mappings',['source_value'])


def downgrade():op.drop_table('department_mappings')
