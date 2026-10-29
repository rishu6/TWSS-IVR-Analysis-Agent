"""Attribute internal audit entries to individual staff accounts."""
from alembic import op
import sqlalchemy as sa

revision='0006'
down_revision='0005'


def upgrade():
    with op.batch_alter_table('audit_logs') as batch:
        batch.add_column(sa.Column('user_id',sa.Integer()))
        batch.create_foreign_key('fk_audit_logs_user_id','users',['user_id'],['id'],ondelete='SET NULL')
        batch.create_index('ix_audit_logs_user_id',['user_id'])


def downgrade():
    with op.batch_alter_table('audit_logs') as batch:
        batch.drop_index('ix_audit_logs_user_id')
        batch.drop_constraint('fk_audit_logs_user_id',type_='foreignkey')
        batch.drop_column('user_id')
