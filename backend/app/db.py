from datetime import UTC, datetime

from sqlalchemy import DateTime, JSON, ForeignKey, Index, String, UniqueConstraint, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def now():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Call(Base):
    __tablename__ = 'calls'
    __table_args__ = (UniqueConstraint('provider', 'provider_call_id'),)
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), default='synthetic')
    provider_call_id: Mapped[str] = mapped_column(String(120))
    caller_e164: Mapped[str | None] = mapped_column(String(20), index=True)
    dialed_did: Mapped[str | None] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(10), default='inbound')
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    final_status: Mapped[str] = mapped_column(String(20), default='UNKNOWN', index=True)
    projection: Mapped[dict] = mapped_column(JSON, default=dict)


class CallEvent(Base):
    __tablename__ = 'call_events'
    __table_args__ = (UniqueConstraint('provider', 'provider_event_id'),
                      Index('ix_call_event_order', 'call_id', 'event_at'))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), default='synthetic')
    provider_event_id: Mapped[str] = mapped_column(String(120))
    call_id: Mapped[str] = mapped_column(ForeignKey('calls.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(30))
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    dedupe_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)


class CallLeg(Base):
    __tablename__ = 'call_legs'
    __table_args__ = (UniqueConstraint('call_id', 'provider_leg_id'),)
    id: Mapped[str] = mapped_column(String(241), primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey('calls.id'), index=True)
    provider_leg_id: Mapped[str] = mapped_column(String(120))
    agent: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120))
    evidence: Mapped[dict] = mapped_column(JSON)


class Lead(Base):
    __tablename__ = 'leads'
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_stage: Mapped[str] = mapped_column(String(80))
    current_owner: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(120))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LeadPhone(Base):
    __tablename__ = 'lead_phone_numbers'
    __table_args__ = (UniqueConstraint('lead_id', 'normalized_number'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey('leads.id'))
    normalized_number: Mapped[str] = mapped_column(String(20), index=True)


class LeadMatch(Base):
    __tablename__ = 'call_lead_matches'
    call_id: Mapped[str] = mapped_column(ForeignKey('calls.id'), primary_key=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey('leads.id'), primary_key=True)
    match_status: Mapped[str] = mapped_column(String(30))
    snapshot_source: Mapped[str] = mapped_column(String(30), default='current only')
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IntegrationEvent(Base):
    __tablename__ = 'integration_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(30))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    status: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(240))


class SyncJob(Base):
    __tablename__ = 'sync_jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(30))
    kind: Mapped[str] = mapped_column(String(30))
    cursor: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(String(240))
    details: Mapped[dict] = mapped_column(JSON,default=dict)


class CallParticipant(Base):
    __tablename__ = 'call_participants'
    id: Mapped[str] = mapped_column(String(64),primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey('calls.id'),index=True)
    agent_name: Mapped[str | None] = mapped_column(String(120),index=True)
    evidence: Mapped[dict] = mapped_column(JSON)


class SessionToken(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(12))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), index=True)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(12))
    active: Mapped[bool] = mapped_column(default=True)
    must_change_password: Mapped[bool] = mapped_column(default=True)
    failed_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IntegrationState(Base):
    __tablename__ = 'integration_state'
    provider: Mapped[str] = mapped_column(String(30), primary_key=True)
    status: Mapped[str] = mapped_column(String(40))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message: Mapped[str | None] = mapped_column(String(240))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class DepartmentMapping(Base):
    __tablename__ = 'department_mappings'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(20))
    source_value: Mapped[str] = mapped_column(String(120),index=True)
    department: Mapped[str] = mapped_column(String(120))
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CRMScanRow(Base):
    __tablename__ = 'crm_scan_rows'
    lead_id: Mapped[str] = mapped_column(String(120),primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class LiveTicket(Base):
    __tablename__ = 'live_tickets'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_hash: Mapped[str] = mapped_column(ForeignKey('sessions.token_hash'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    role: Mapped[str] = mapped_column(String(12))
    action: Mapped[str] = mapped_column(String(80))
    resource: Mapped[str] = mapped_column(String(120))
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)


def database(url):
    kwargs = {'connect_args': {'check_same_thread': False, 'timeout':30}} if url.startswith('sqlite') else {}
    engine = create_engine(url, **kwargs)
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def sqlite_foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=30000')
    return engine, sessionmaker(engine, expire_on_commit=False)
