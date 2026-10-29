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
