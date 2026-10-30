from dataclasses import replace
from sqlalchemy import select
import httpx
from app.db import Call,Lead,LeadPhone
from app.cdr import store_record
from app.live_sync import LiveSync
from app.crm_analytics import analytics
from app.provider_clients import LiveLeadSquaredClient
from test_internal import internal,cdr


def test_phone_search_checks_both_fields_and_deduplicates():
    import json
    fields=[]
    def response(request):
        body=json.loads(request.content);fields.append(body['Parameter']['LookupName'])
        assert body['Parameter']['SqlOperator']=='LIKE'
        assert body['Paging']['PageSize']==1000
        return httpx.Response(200,json=[{'ProspectID':'one'},{'ProspectID':'two'}])
    client=LiveLeadSquaredClient({'LEADSQUARED_API_HOST':'https://api.leadsquared.com',
        'LEADSQUARED_ACCESS_KEY':'fake','LEADSQUARED_SECRET_KEY':'fake'},
        transport=httpx.MockTransport(response),interval=0)
    assert len(client.phone_candidates('+12025550101'))==2
    assert fields==['Phone','Mobile']
    client.close()


def test_pending_caller_is_matched_without_full_index(internal,monkeypatch):
    from app import live_sync
    class CRM:
        def __init__(self,*args):pass
        def phone_candidates(self,phone):
            return [dict(ProspectID=key,FirstName='Test',CreatedOn='2026-10-01 00:00:00',
                Phone=number,Mobile=None,OwnerId='Owner',ProspectStage='New')
                for key,number in [('actual','+12025550101'),('same-suffix','+442079460101')]]
        def close(self):pass
    monkeypatch.setattr(live_sync,'LiveLeadSquaredClient',CRM)
    monkeypatch.setattr(live_sync,'load_credentials',lambda _: {})
    with internal.app.state.sessions.begin() as db:store_record(db,cdr(call_flow=[{'type':'init','time':1700000000},{'type':'Department','name':'Admissions','time':1700000001},{'type':'hangup','time':1700000100}]))
    worker=LiveSync(internal.app.state.settings,internal.app.state.sessions)
    assert worker.run_matches()['status']=='FINISHED'
    with internal.app.state.sessions() as db:
        call=db.scalar(select(Call));crm=call.projection['crm']
        assert crm['status']=='MATCHED'
        assert [l['id'] for l in crm['candidates']]==['actual']
        assert crm['phone_checked_at']
        assert db.get(Lead,'same-suffix') is None


def test_report_uses_positive_index_match_for_pending_call(internal):
    from datetime import UTC,datetime
    with internal.app.state.sessions.begin() as db:
        store_record(db,cdr(call_flow=[{'type':'init','time':1700000000},{'type':'Department','name':'Admissions','time':1700000001},{'type':'hangup','time':1700000100}]))
        db.add(Lead(id='indexed',display_name='Existing lead',created_at=datetime(2026,1,1,tzinfo=UTC),
            current_stage='Qualified',current_owner='Owner',source='Test'))
        db.flush();db.add(LeadPhone(lead_id='indexed',normalized_number='+12025550101'));db.flush()
        summary,rows=analytics(db,db.scalars(select(Call)).all(),'Admin')
        assert summary['matched_callers']==1 and summary['unresolved_callers']==0
        assert rows[0]['candidates'][0]['current_stage']=='Qualified'


def test_direct_phone_match_survives_older_index_refresh(internal):
    from datetime import UTC,datetime
    with internal.app.state.sessions.begin() as db:
        store_record(db,cdr())
        call=db.scalar(select(Call))
        call.projection={**call.projection,'crm':{'status':'MATCHED',
            'candidates':[{'id':'fresh'}],'phone_checked_at':'2026-10-29T12:00:00+00:00'}}
    worker=LiveSync(internal.app.state.settings,internal.app.state.sessions)
    worker.enrich_calls(True,datetime(2026,10,29,10,tzinfo=UTC))
    with internal.app.state.sessions() as db:
        assert db.scalar(select(Call)).projection['crm']['candidates']==[{'id':'fresh'}]


def test_unchanged_crm_calls_do_not_reload_full_journeys(internal):
    from datetime import UTC,datetime
    from sqlalchemy import event
    from app.db import IntegrationState
    stamp=datetime(2026,10,30,0,0,tzinfo=UTC)
    with internal.app.state.sessions.begin() as db:
        store_record(db,cdr())
        call=db.scalar(select(Call))
        call.projection={**call.projection,'crm':{'status':'MATCHED','candidates':[],
            'synced_at':stamp.isoformat(),'stale':False}}
        db.add(IntegrationState(provider='leadsquared',status='HEALTHY',details={}))
    statements=[]
    def capture(connection,cursor,statement,parameters,context,many):statements.append(statement)
    engine=internal.app.state.engine
    event.listen(engine,'before_cursor_execute',capture)
    try:LiveSync(internal.app.state.settings,internal.app.state.sessions).enrich_calls(True,stamp)
    finally:event.remove(engine,'before_cursor_execute',capture)
    assert not any('SELECT calls.id, calls.provider' in statement for statement in statements)
    assert not any(statement.lstrip().upper().startswith(('UPDATE','DELETE','INSERT')) for statement in statements)
