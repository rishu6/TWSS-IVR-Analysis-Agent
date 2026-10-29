"""Durable history imports and provider-evidenced call participants (not call legs)."""
from alembic import op
import sqlalchemy as sa

revision='0007'
down_revision='0006'


def upgrade():
    op.add_column('sync_jobs',sa.Column('details',sa.JSON(),nullable=False,server_default='{}'))
    op.create_table('call_participants',sa.Column('id',sa.String(64),primary_key=True),
        sa.Column('call_id',sa.String(120),sa.ForeignKey('calls.id'),nullable=False),
        sa.Column('agent_name',sa.String(120)),sa.Column('evidence',sa.JSON(),nullable=False))
    op.create_index('ix_call_participants_call_id','call_participants',['call_id'])
    op.create_index('ix_call_participants_agent_name','call_participants',['agent_name'])


def downgrade():
    op.drop_table('call_participants')
    with op.batch_alter_table('sync_jobs') as batch:batch.drop_column('details')
