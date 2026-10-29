"""Preserve identified calls when caller/DID normalization is unavailable."""
from alembic import op
import sqlalchemy as sa

revision='0005'
down_revision='0004'


def upgrade():
    with op.batch_alter_table('calls') as batch:
        batch.alter_column('caller_e164',existing_type=sa.String(20),nullable=True)
        batch.alter_column('dialed_did',existing_type=sa.String(20),nullable=True)


def downgrade():
    connection=op.get_bind()
    if connection.execute(sa.text('SELECT COUNT(*) FROM calls WHERE caller_e164 IS NULL OR dialed_did IS NULL')).scalar():
        raise RuntimeError('Cannot discard calls with unknown phone evidence during downgrade')
    with op.batch_alter_table('calls') as batch:
        batch.alter_column('caller_e164',existing_type=sa.String(20),nullable=False)
        batch.alter_column('dialed_did',existing_type=sa.String(20),nullable=False)
