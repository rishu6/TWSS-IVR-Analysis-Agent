"""Individual identities and durable provider health."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'


def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(120), nullable=False, unique=True),
        sa.Column('display_name', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(12), nullable=False), sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('must_change_password', sa.Boolean(), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    with op.batch_alter_table('sessions') as batch:
        batch.add_column(sa.Column('user_id', sa.Integer()))
        batch.create_foreign_key('fk_sessions_user_id', 'users', ['user_id'], ['id'])
        batch.create_index('ix_sessions_user_id', ['user_id'])
    op.create_table('integration_state', sa.Column('provider', sa.String(30), primary_key=True),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('last_success_at', sa.DateTime(timezone=True)),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True)),
        sa.Column('message', sa.String(240)), sa.Column('details', sa.JSON(), nullable=False))


def downgrade():
    op.drop_table('integration_state')
    with op.batch_alter_table('sessions') as batch:
        batch.drop_index('ix_sessions_user_id')
        batch.drop_constraint('fk_sessions_user_id', type_='foreignkey')
        batch.drop_column('user_id')
    op.drop_table('users')
