"""Durable staging for large CRM phone-index scans."""
from alembic import op
import sqlalchemy as sa

revision='0004'
down_revision='0003'


def upgrade():
    op.create_table('crm_scan_rows',sa.Column('lead_id',sa.String(120),primary_key=True),sa.Column('payload',sa.JSON(),nullable=False))


def downgrade():op.drop_table('crm_scan_rows')
