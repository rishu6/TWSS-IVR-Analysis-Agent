from datetime import UTC,datetime,time,timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func,select

from app import history
from app.cdr import project_record,store_record
from app.db import Call,CallEvent,CallParticipant,SyncJob
from app.live_sync import LiveSync
from app.provider_clients import LiveAcefoneClient
from app.reports import filtered_query,present
from test_internal import internal,sign_in,cdr,CSRF


def agent_flow():
    return cdr(department_name=None,agent_name=None,date='2023-11-15',time='03:43:20',call_duration=105,
        missed_agents=[{'name':'First Agent','number':'+12025550102'}],call_flow=[
            {'type':'init','time':1700000002},
            {'type':'Department','name':'Admissions','time':1700000003},
            {'type':'Agent','id':'agent-1','name':'First Agent','num':'+12025550102','dialst':'Dialed','time':1700000004},
            {'type':'Agent','id':'agent-2','name':'Final Agent','num':'+12025550103','dialst':'Dialed','time':1700000010},
            {'type':'Agent','id':'agent-2','name':'Final Agent','number':'+12025550103','dialst':'Answered','time':1700000015},
            {'type':'Department','name':'Support','time':1700000020},
            {'type':'hangup','time':1700000100}])


def test_complete_provider_evidence_without_invented_ring_legs():
    result=project_record(agent_flow())
    assert result['answering_agent']=='Final Agent'
    assert result['departments']==['Admissions','Support']
    assert result['primary_department']=='Admissions'
    assert result['reported_missed_agents'][0]['agent_name']=='First Agent'
    assert result['reported_missed_agents'][0]['missed_at'] is None
    assert result['ring_attempts'] is None and result['legs']==[]
    assert result['duration_seconds']==105
    assert result['started_at']=='2023-11-14T22:13:20+00:00'
    assert next(e for e in result['events'] if e.get('disposition')=='Answered')['agent']=='Final Agent'


def test_participant_search_and_viewer_phone_masking(internal):
    with internal.app.state.sessions.begin() as db:
        store_record(db,agent_flow())
        assert len(db.scalars(filtered_query(agent='First Agent')).all())==1
        assert len(db.scalars(filtered_query(q='First Agent')).all())==1
        assert db.scalar(select(func.count()).select_from(CallParticipant))==2
        result=present(db.scalar(select(Call)),'Viewer',journey=True)
        assert '+1202555' not in str(result)
        assert result['reported_missed_agents'][0]['agent_name']=='First Agent'


def job_for_yesterday(sessions):
    zone=ZoneInfo('Asia/Kolkata');day=datetime.now(zone).date()-timedelta(days=1)
    start=datetime.combine(day,time.min,zone);end=start+timedelta(days=1)
    with sessions.begin() as db:
        job=SyncJob(provider='acefone',kind='history',status='QUEUED',details={
            'from_date':str(day),'through_date':str(day),'range_start':start.astimezone(UTC).isoformat(),
            'range_end':end.astimezone(UTC).isoformat(),'next_date':str(day),'direction_index':0,'next_page':1,
            'records_seen':0,'changed_calls':0,'rejected_records':0,'completed_days':[]})
        db.add(job);db.flush();return job.id


def test_history_resumes_from_durable_page_and_fetches_both_directions(internal,monkeypatch):
    calls=[]
    class FakeCDR:
        def __init__(self,*a,**k):pass
        def record_page(self,start,end,page,direction):
            calls.append((direction,page,start.hour,end.hour,end.second))
            rows=[cdr(call_id=f'provider-{page}')] if direction=='inbound' and page<=11 else []
            return {'rows':rows,'has_more':bool(rows),'limit':1,'page':page}
        def close(self):pass
    monkeypatch.setattr(history,'LiveAcefoneClient',FakeCDR)
    sessions=internal.app.state.sessions;id=job_for_yesterday(sessions)
    worker=LiveSync(internal.app.state.settings,sessions)
    assert history.process_history(worker,{'ACEFONE_API_TOKEN':'test'})
    with sessions() as db:
        job=db.get(SyncJob,id)
        assert job.status=='RUNNING' and job.details['next_page']==11
    assert history.process_history(LiveSync(internal.app.state.settings,sessions),{'ACEFONE_API_TOKEN':'test'})
    with sessions() as db:
        job=db.get(SyncJob,id)
        assert job.status=='SUCCEEDED' and job.details['records_seen']==11
        assert db.scalar(select(func.count()).select_from(Call))==11
    assert ('outbound',1,0,23,59) in calls
    assert [p for d,p,*_ in calls if d=='inbound']==list(range(1,13))


def test_repeated_provider_page_never_marks_range_complete(internal,monkeypatch):
    class RepeatedCDR:
        def __init__(self,*a,**k):pass
        def record_page(self,*a,**k):return {'rows':[cdr()],'has_more':True,'limit':1}
        def close(self):pass
    monkeypatch.setattr(history,'LiveAcefoneClient',RepeatedCDR)
    id=job_for_yesterday(internal.app.state.sessions)
    history.process_history(LiveSync(internal.app.state.settings,internal.app.state.sessions),{'ACEFONE_API_TOKEN':'test'})
    with internal.app.state.sessions() as db:
        job=db.get(SyncJob,id)
        assert job.status=='ERROR' and 'repeated' in job.error


def test_history_request_permissions_and_calendar_boundaries(internal):
    internal.app.state.live_sync=SimpleNamespace(run=lambda:None)
    yesterday=datetime.now(ZoneInfo('Asia/Kolkata')).date()-timedelta(days=1)
    body={'from_date':str(yesterday),'through_date':str(yesterday)}
    sign_in(internal,'viewer','viewer-password-123')
    assert internal.post('/api/v1/history/import',headers=CSRF,json=body).status_code==403
    sign_in(internal)
    internal.post('/api/v1/auth/change-password',headers=CSRF,json={
        'current_password':'temporary-password-123','new_password':'new-history-password-456'})
    result=internal.post('/api/v1/history/import',headers=CSRF,json=body)
    assert result.status_code==200
    details=result.json()['details']
    expected=datetime.combine(yesterday,time.min,ZoneInfo('Asia/Kolkata')).astimezone(UTC).isoformat()
    assert details['range_start']==expected
    assert (datetime.fromisoformat(details['range_end'])-datetime.fromisoformat(details['range_start'])).total_seconds()==86400
    assert internal.post('/api/v1/history/import',headers=CSRF,json=body).json()['id']==result.json()['id']


def test_reprojection_upgrades_flow_without_duplicate_snapshot(internal):
    with internal.app.state.sessions.begin() as db:
        store_record(db,agent_flow());call=db.scalar(select(Call))
        call.projection={**call.projection,'projection_version':1,'participants':[]}
        store_record(db,agent_flow())
        assert len(call.projection['participants'])==2
        assert db.scalar(select(func.count()).select_from(CallEvent))==1


def test_answerer_uses_latest_timestamp_not_array_order_or_cdr_name():
    record=agent_flow()
    record['agent_name']='Stale CDR Agent'
    record['call_flow'].insert(0,{'type':'Agent','name':'Transferred Answerer','id':'agent-3','dialst':'Answered','time':1700000050})
    result=project_record(record)
    assert result['answering_agent']=='Transferred Answerer'
    assert result['answering_agent_source']=='last_answer_event'
    assert result['status']=='ANSWERED'


def test_unnamed_latest_answer_resolves_only_from_supplied_identity():
    record=agent_flow()
    record['call_flow'].append({'type':'Agent','id':'agent-2','dialst':'Answered','time':1700000050})
    result=project_record(record)
    assert result['answering_agent']=='Final Agent'
    assert result['answering_agent_source']=='last_answer_event'


def test_simultaneous_answerers_use_labelled_cdr_fallback_and_preserve_missed_outcome():
    record=agent_flow()
    record['agent_name']='CDR Agent'
    record['call_flow'].append({'type':'Agent','name':'Other Agent','dialst':'Answered','time':1700000015})
    result=project_record(record)
    assert result['answering_agent']=='CDR Agent'
    assert result['answering_agent_source']=='provider_cdr'
    record['status']='missed'
    result=project_record(record)
    assert result['status']=='MISSED'
    assert result['answering_agent'] is None
    assert result['answering_agent_source'] is None


def test_missed_metrics_require_flow_department_and_respect_combined_filters(internal):
    base=agent_flow()
    without_department=[e for e in base['call_flow'] if e['type']!='Department']
    cases=[
        ('selected',dict(status='missed')),
        ('repeat-caller',dict(status='missed')),
        ('ivr-exit',dict(status='missed',call_flow=[{'type':'init','time':1700000002},{'type':'IVR','name':'Menu','time':1700000003},{'type':'hangup','time':1700000100} ],department_name=None)),
        ('label-only',dict(status='missed',call_flow=without_department,department_name='Admissions')),
        ('dtmf-only',dict(status='missed',call_flow=without_department,dtmf_input='1')),
        ('answered',dict(status='answered')),
        ('outbound',dict(status='missed',direction='outbound')),
    ]
    with internal.app.state.sessions.begin() as db:
        for name,changes in cases:
            store_record(db,{**base,'call_id':name,**changes})
    sign_in(internal,'viewer','viewer-password-123')
    response=internal.get('/api/v1/metrics/overview')
    assert response.status_code==200
    data=response.json()
    assert data['total']==6
    assert data['MISSED']==5
    assert data['customer_missed']==2  # logical calls, even when the caller repeats
    assert data['missed_without_department']==3
    assert sum(h['customer_missed'] for h in data['hourly'])==2
    assert sum(h['missed'] for h in data['hourly'])==5
    filtered=internal.get('/api/v1/metrics/overview',params={
        'department':'Admissions','outcome':'MISSED','start':'2023-11-14T18:30:00Z','end':'2023-11-15T18:30:00Z'}).json()
    assert filtered['MISSED']==3 and filtered['customer_missed']==2
    empty=internal.get('/api/v1/metrics/overview?start=2026-01-01T00:00:00Z').json()
    assert empty['customer_missed']==0 and empty['MISSED']==0


def test_department_missed_button_filters_before_pagination(internal):
    base=agent_flow()
    with internal.app.state.sessions.begin() as db:
        store_record(db,{**base,'call_id':'selected','status':'missed'})
        store_record(db,{**base,'call_id':'no-selection','status':'missed','call_flow':[],'department_name':'Admissions'})
        store_record(db,{**base,'call_id':'answered','status':'answered'})
    sign_in(internal,'viewer','viewer-password-123')
    summary=internal.get('/api/v1/calls-summary').json()
    assert summary['outcomes']['MISSED']==2 and summary['missed_department']==1
    data=internal.get('/api/v1/calls?missed_department=true&page_size=1').json()
    assert data['total']==1 and data['next_page'] is None
    assert data['items'][0]['provider_call_id']=='selected'
    assert internal.get('/api/v1/calls?missed_department=true&page=2').json()['items']==[]
    sign_in(internal)
    internal.post('/api/v1/auth/change-password',headers=CSRF,json={'current_password':'temporary-password-123','new_password':'export-test-password-456'})
    exported=internal.get('/api/v1/reports/exports?missed_department=true')
    assert exported.status_code==200 and len(exported.text.splitlines())==2
