from datetime import timedelta
from types import SimpleNamespace

from app.demo_data import fixtures
from app.domain import reduce_events
from app.reports import recovery_candidates


def records():
    ids = {event.call_id for event in fixtures()}
    return [SimpleNamespace(projection=reduce_events([e for e in fixtures() if e.call_id == id])) for id in sorted(ids)]


def test_recovery_candidate_does_not_change_missed_outcome():
    calls = records()
    result = recovery_candidates(calls, hours=24)
    assert result[0]['call_id'] == 'demo-missed'
    assert result[0]['status'] == 'RECOVERY_CANDIDATE'
    assert result[0]['recovery_call_id'] == 'demo-callback'
    assert next(c for c in calls if c.projection['id']=='demo-missed').projection['status'] == 'MISSED'


def test_different_did_or_expired_window_never_matches():
    calls = records()
    callback = next(c for c in calls if c.projection['id'] == 'demo-callback')
    callback.projection['did'] = '+12025550198'
    assert recovery_candidates(calls, 24)[0]['status'] == 'UNRECOVERED'
    callback.projection['did'] = '+12025550199'
    assert recovery_candidates(calls, 0.01)[0]['status'] == 'UNRECOVERED'


def test_one_connected_call_not_reused():
    calls = records()
    missed = next(c for c in calls if c.projection['id']=='demo-missed')
    copy = SimpleNamespace(projection={**missed.projection, 'id':'demo-another-missed'})
    result = recovery_candidates(calls+[copy], 24)
    assert sum(r['status']=='RECOVERY_CANDIDATE' for r in result) == 1
