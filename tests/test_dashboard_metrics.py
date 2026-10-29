from sqlalchemy import select
from app.reports import overview,department_report
from app.cdr import store_record
from app.db import Call
from test_internal import internal,cdr
from test_crm_analytics import add


def test_dashboard_unique_callers_and_department_outcomes(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'answered');add(db,'repeat')
        add(db,'missed',phone='+12025550102',status='missed')
        add(db,'hidden',phone='anonymous',status='missed')
        store_record(db,cdr(call_id='outbound',direction='outbound'))
        calls=db.scalars(select(Call)).all()
        data=overview(calls)
        assert data['total']==4 and data['unique_callers']==2
        assert data['ANSWERED']==2 and data['MISSED']==2
        rows=department_report(calls)
        assert rows==[dict(department='Admissions',primary_calls=4,involved_calls=4,answered_primary=2,missed_primary=2)]


def test_answer_rate_excludes_calls_without_recorded_department(internal):
    from test_internal import sign_in
    with internal.app.state.sessions.begin() as db:
        add(db,'selected-answered');add(db,'selected-answered-repeat')
        add(db,'selected-missed',status='missed')
        add(db,'no-selection-answer',department=False)
        add(db,'no-selection-missed',department=False,status='missed')
        # A reporting label alone does not prove department selection.
        store_record(db,cdr(call_id='label-only',department_name='Admissions'))
    sign_in(internal,'viewer','viewer-password-123')
    metric=internal.get('/api/v1/metrics/overview').json()
    assert metric['total']==6 and metric['ANSWERED']==4
    assert metric['department_calls']==3 and metric['department_answered']==2
    assert metric['answer_rate']==2/3
    assert metric['overall_answer_rate']==4/6
    result=internal.get('/api/v1/calls?department_selected=true&outcome=ANSWERED&page_size=1').json()
    assert result['total']==2 and len(result['items'])==1 and result['next_page']==2
    assert result['items'][0]['provider_call_id'] in ['selected-answered','selected-answered-repeat']
    counts=internal.get('/api/v1/calls-summary?department_selected=true&outcome=ANSWERED').json()
    assert counts['total']==3 and counts['outcomes']=={'ANSWERED':2,'MISSED':1}
    filtered=internal.get('/api/v1/metrics/overview?outcome=MISSED').json()
    assert filtered['department_calls']==1 and filtered['answer_rate']==0


def test_answer_rate_is_unavailable_when_no_department_was_selected(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'ivr-only',department=False)
        metric=overview(db.scalars(select(Call)).all())
        assert metric['department_calls']==0 and metric['department_answered']==0
        assert metric['answer_rate'] is None
        assert metric['overall_answer_rate']==1
