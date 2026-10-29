import random
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.db import Call, CallEvent
from app.demo_data import fixtures, four_agents, scenario
from app.domain import reduce_events, timestamp
from app.ingestion import ingest


def test_A_three_misses_fourth_answers():
    call = reduce_events(four_agents())
    assert call['status'] == 'ANSWERED'
    assert call['missed_attempts'] == 3
    assert call['ring_attempts'] == 4
    assert sum(leg['disposition'] == 'ANSWERED' for leg in call['legs']) == 1
    assert call['answering_agent'] == 'Dev Patel'
    assert call['first_response_seconds'] == 80
    assert call['status'] != 'MISSED'


def test_B_ivr_exit_no_invented_misses():
    call = reduce_events([e for e in fixtures() if e.call_id == 'demo-ivr-exit'])
    assert call['status'] == 'IVR_ONLY'
    assert call['legs'] == []
    assert call['missed_attempts'] == 0


def test_C_transfer_preserves_call_and_departments():
    call = reduce_events([e for e in fixtures() if e.call_id == 'demo-transfer'])
    assert len(call['legs']) == 2
    assert call['departments'] == ['Sales', 'Support']
    assert call['primary_department'] == 'Sales'
    assert call['transfers'][0]['source_leg_id'] == 'sales-leg'


def test_D_permutations_and_duplicate_storage(client):
    expected = reduce_events(four_agents())
    for seed in range(20):
        shuffled = four_agents()
        random.Random(seed).shuffle(shuffled)
        assert reduce_events(shuffled) == expected
    with client.app.state.sessions.begin() as db:
        ingest(db, list(reversed(four_agents())) + four_agents())
        assert db.scalar(select(func.count()).select_from(Call)) == 1
        assert db.scalar(select(func.count()).select_from(CallEvent)) == len(four_agents())


def test_G_unknown_ring_coverage_is_null():
    call = reduce_events([e for e in fixtures() if e.call_id == 'demo-no-ring-data'])
    assert call['ring_attempts'] is None
    assert call['missed_attempts'] is None
    assert call['status'] == 'ANSWERED'


def test_H_offset_normalizes_to_kolkata():
    event = four_agents()[0].model_copy(update={'at': timestamp('2026-10-26T23:30:00-05:00')})
    call = reduce_events([event])
    displayed = timestamp(call['started_at']).astimezone(ZoneInfo('Asia/Kolkata'))
    assert displayed.strftime('%Y-%m-%d %H:%M') == '2026-10-27 10:00'


def test_J_reconcile_retains_event_history(client):
    events = four_agents()
    sessions = client.app.state.sessions
    with sessions.begin() as db:
        ingest(db, events[:3])
        assert db.get(Call, 'demo-four-agents').final_status == 'IN_PROGRESS'
    with sessions.begin() as db:
        ingest(db, events)
        assert db.get(Call, 'demo-four-agents').final_status == 'ANSWERED'
        assert db.scalar(select(func.count()).select_from(CallEvent)) == len(events)


def test_phone_and_time_do_not_merge_calls(client):
    one = scenario('demo-one', '+12025550101', [(0, 'INBOUND', {})])
    two = scenario('demo-two', '+12025550101', [(0, 'INBOUND', {})])
    with client.app.state.sessions.begin() as db:
        ingest(db, one + two)
        assert db.scalar(select(func.count()).select_from(Call)) == 2


def test_clock_skew_is_partial_not_negative_duration():
    events = four_agents()
    events[0] = events[0].model_copy(update={'at': events[-1].at + timedelta(seconds=10)})
    call = reduce_events(events)
    assert call['duration_seconds'] is None
    assert 'End predates inbound start' in call['warnings']
