"""Synthetic demo foundation; live-domain extensions require subsequent migrations."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None


def upgrade():
    op.create_table('calls', sa.Column('id', sa.String(120), primary_key=True),
        sa.Column('provider', sa.String(30), nullable=False), sa.Column('provider_call_id', sa.String(120), nullable=False),
        sa.Column('caller_e164', sa.String(20), nullable=False), sa.Column('dialed_did', sa.String(20), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False), sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('final_status', sa.String(20), nullable=False), sa.Column('projection', sa.JSON(), nullable=False),
        sa.UniqueConstraint('provider', 'provider_call_id'))
    for column in ('caller_e164', 'dialed_did', 'started_at', 'final_status'):
        op.create_index('ix_calls_' + column, 'calls', [column])
    op.create_table('call_events', sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('provider', sa.String(30), nullable=False), sa.Column('provider_event_id', sa.String(120), nullable=False),
        sa.Column('call_id', sa.String(120), sa.ForeignKey('calls.id'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False), sa.Column('event_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False), sa.Column('dedupe_hash', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False), sa.UniqueConstraint('provider', 'provider_event_id'))
    op.create_index('ix_call_events_call_id', 'call_events', ['call_id'])
    op.create_index('ix_call_event_order', 'call_events', ['call_id', 'event_at'])
    op.create_table('call_legs', sa.Column('id', sa.String(241), primary_key=True),
        sa.Column('call_id', sa.String(120), sa.ForeignKey('calls.id'), nullable=False),
        sa.Column('provider_leg_id', sa.String(120), nullable=False), sa.Column('agent', sa.String(120)),
        sa.Column('department', sa.String(120)), sa.Column('evidence', sa.JSON(), nullable=False),
        sa.UniqueConstraint('call_id', 'provider_leg_id'))
    op.create_index('ix_call_legs_call_id', 'call_legs', ['call_id'])
    op.create_table('leads', sa.Column('id', sa.String(120), primary_key=True),
        sa.Column('display_name', sa.String(120), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_stage', sa.String(80), nullable=False), sa.Column('current_owner', sa.String(120), nullable=False),
        sa.Column('source', sa.String(120), nullable=False), sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('lead_phone_numbers', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('lead_id', sa.String(120), sa.ForeignKey('leads.id'), nullable=False),
        sa.Column('normalized_number', sa.String(20), nullable=False), sa.UniqueConstraint('lead_id', 'normalized_number'))
    op.create_index('ix_lead_phone_numbers_normalized_number', 'lead_phone_numbers', ['normalized_number'])
    op.create_table('call_lead_matches', sa.Column('call_id', sa.String(120), sa.ForeignKey('calls.id'), primary_key=True),
        sa.Column('lead_id', sa.String(120), sa.ForeignKey('leads.id'), primary_key=True),
        sa.Column('match_status', sa.String(30), nullable=False), sa.Column('snapshot_source', sa.String(30), nullable=False),
        sa.Column('matched_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('integration_events', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(30), nullable=False), sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False), sa.Column('payload', sa.JSON(), nullable=False), sa.Column('error', sa.String(240)))
    op.create_table('sync_jobs', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(30), nullable=False), sa.Column('kind', sa.String(30), nullable=False),
        sa.Column('cursor', sa.String(120)), sa.Column('status', sa.String(30), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False), sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error', sa.String(240)))
    op.create_table('sessions', sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('role', sa.String(12), nullable=False), sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_sessions_expires_at', 'sessions', ['expires_at'])
    op.create_table('live_tickets', sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('session_hash', sa.String(64), sa.ForeignKey('sessions.token_hash'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('audit_logs', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False), sa.Column('role', sa.String(12), nullable=False),
        sa.Column('action', sa.String(80), nullable=False), sa.Column('resource', sa.String(120), nullable=False))


def downgrade():
    for table in ('audit_logs', 'live_tickets', 'sessions', 'sync_jobs', 'integration_events',
                  'call_lead_matches', 'lead_phone_numbers', 'leads', 'call_legs', 'call_events', 'calls'):
        op.drop_table(table)
