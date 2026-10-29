from sqlalchemy import func, select
import pytest

from app.adapters import LiveAcefoneClient, LiveLeadSquaredClient, SyntheticAcefoneClient
from app.db import Call, CallEvent, SyncJob
from app.domain import Event
from app.auth import utc
from app.ingestion import backfill, ingest


def event(event_id='e1', **values):
    return Event(event_id=event_id, call_id='demo-one', caller='+12025550101', did='+12025550199',
                 type='INBOUND', at='2026-10-27T10:00:00+05:30', **values)


def test_duplicates_conflicts_and_rollback(client):
    sessions = client.app.state.sessions
    with sessions.begin() as db:
        assert ingest(db, [event(), event()]) == {'accepted': 1, 'duplicates': 1}
    with pytest.raises(ValueError, match='Conflicting payload'):
        with sessions.begin() as db:
            ingest(db, [event(sequence=1)])
    with sessions() as db:
        assert db.scalar(select(func.count()).select_from(CallEvent)) == 1
        assert db.scalar(select(func.count()).select_from(Call)) == 1


def test_backfill_pages_are_idempotent(client):
    sessions = client.app.state.sessions
    adapter = SyntheticAcefoneClient([event('e1'), event('e2')], page_size=1)
    backfill(sessions, adapter)
    backfill(sessions, adapter, kind='reconciliation')
    with sessions() as db:
        assert db.scalar(select(func.count()).select_from(CallEvent)) == 2
        assert all(j.status == 'SUCCEEDED' for j in db.scalars(select(SyncJob)))


def test_live_adapters_fail_closed():
    for adapter in (LiveAcefoneClient, LiveLeadSquaredClient):
        with pytest.raises(RuntimeError, match='unverified'):
            adapter()


def test_offset_is_persisted_as_utc(client):
    with client.app.state.sessions.begin() as db:
        ingest(db, [event()])
        root = db.get(Call, 'demo-one')
        assert utc(root.started_at).isoformat() == '2026-10-27T04:30:00+00:00'
        stored = db.scalar(select(CallEvent))
        assert stored.payload['at'].endswith('+05:30')  # Original offset is retained.
