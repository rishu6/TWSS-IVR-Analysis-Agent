from datetime import timedelta

import pytest
from sqlalchemy import select

from app.adapters import SyntheticLeadSquaredClient
from app.crm import enrich, normalize_phone
from app.db import Call, LeadMatch
from app.demo_data import fixtures, leads
from app.ingestion import ingest
from app.db import now


@pytest.mark.parametrize('raw', ['98765 43210', '+91-98765-43210', '09876543210'])
def test_india_normalization(raw):
    assert normalize_phone(raw) == '+919876543210'


def test_invalid_phone_rejected():
    with pytest.raises(ValueError):
        normalize_phone('not-a-phone')


def test_E_all_duplicate_candidates_stored(client):
    with client.app.state.sessions.begin() as db:
        ingest(db, [e for e in fixtures() if e.call_id == 'demo-missed'])
        result = enrich(db, db.get(Call, 'demo-missed'), SyntheticLeadSquaredClient(leads()))
        assert result['status'] == 'MULTIPLE_MATCHES'
        assert len(result['candidates']) == 2
        assert len(db.scalars(select(LeadMatch)).all()) == 2
        assert result['snapshot_source'] == 'current only'


def test_F_crm_failure_does_not_affect_telephony_and_retries(client):
    with client.app.state.sessions.begin() as db:
        ingest(db, [e for e in fixtures() if e.call_id == 'demo-four-agents'])
        call = db.get(Call, 'demo-four-agents')
        clock = now()
        adapter = SyntheticLeadSquaredClient(leads(), unavailable=True)
        result = enrich(db, call, adapter, clock=clock)
        assert result['status'] == 'ERROR'
        assert call.final_status == 'ANSWERED'
        assert enrich(db, call, adapter, clock=clock)['attempts'] == 1  # backoff
        adapter.unavailable = False
        result = enrich(db, call, adapter, clock=clock + timedelta(seconds=31))
        assert result['status'] == 'MATCHED'


def test_retry_exhaustion_is_bounded(client):
    with client.app.state.sessions.begin() as db:
        ingest(db, fixtures()[:1])
        call = db.get(Call, 'demo-four-agents')
        clock = now()
        adapter = SyntheticLeadSquaredClient([], unavailable=True)
        for attempt in range(8):
            result = enrich(db, call, adapter, clock=clock + timedelta(hours=attempt))
        assert result['status'] == 'ERROR_RETRY_EXHAUSTED'
        assert result['attempts'] == 5
