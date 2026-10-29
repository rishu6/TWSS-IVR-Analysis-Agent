import sqlite3
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.db import Base, Call, CallEvent, User
from app.main import create_app
from app.passwords import hash_password
from app.cdr import project_record, store_record
from app.provider_clients import LiveAcefoneClient, LiveLeadSquaredClient, ProviderError, ReadOnlyTransport

CSRF={'x-csrf-protection':'1'}


@pytest.fixture
def internal(tmp_path):
    app=create_app(Settings(mode='internal',database_url=f'sqlite:///{tmp_path}/internal.db',auto_sync=False))
    Base.metadata.create_all(app.state.engine)
    with app.state.sessions.begin() as db:
        db.add(User(username='localadmin',display_name='Local Admin',password_hash=hash_password('temporary-password-123'),
                    role='Admin',active=True,must_change_password=True,failed_attempts=0))
        db.add(User(username='viewer',display_name='Viewer',password_hash=hash_password('viewer-password-123'),
                    role='Viewer',active=True,must_change_password=False,failed_attempts=0))
    with TestClient(app) as client:yield client


def sign_in(client,user='localadmin',password='temporary-password-123'):
    return client.post('/api/v1/auth/login',headers=CSRF,json={'username':user,'password':password,'role':'Admin'})


def test_temporary_password_gates_customer_data(internal):
    assert internal.get('/api/v1/auth/configuration').json()['demo'] is False
    assert sign_in(internal).json()['must_change_password']
    assert internal.get('/api/v1/calls').status_code==403
    changed=internal.post('/api/v1/auth/change-password',headers=CSRF,json={
        'current_password':'temporary-password-123','new_password':'new-internal-password-456'})
    assert changed.status_code==200
    assert internal.get('/api/v1/calls').status_code==200
    assert internal.post('/api/v1/demo/retry-crm',headers=CSRF).status_code==403
    assert internal.get('/api/v1/integrations/health').json()['synthetic'] is False


def test_client_cannot_choose_admin_role(internal):
    assert sign_in(internal,'viewer','viewer-password-123').json()['role']=='Viewer'
    assert internal.get('/api/v1/admin/users').status_code==403
    assert internal.get('/api/v1/reports/exports').status_code==403


def test_lockout_after_five_failures(internal):
    for _ in range(5):assert sign_in(internal,'viewer','incorrect').status_code==401
    assert sign_in(internal,'viewer','viewer-password-123').status_code==401


def test_account_management_last_admin_and_session_revocation(internal):
    sign_in(internal)
    internal.post('/api/v1/auth/change-password',headers=CSRF,json={
        'current_password':'temporary-password-123','new_password':'new-internal-password-456'})
    users=internal.get('/api/v1/admin/users').json()['items']
    admin=next(u for u in users if u['username']=='localadmin')
    assert internal.patch(f'/api/v1/admin/users/{admin["id"]}',headers=CSRF,json={'active':False}).status_code==409
    response=internal.post('/api/v1/admin/users',headers=CSRF,json={
        'username':'manager','display_name':'Manager','role':'Manager','password':'staff-temporary-password'})
    assert response.status_code==200 and 'password_hash' not in response.text
    viewer=next(u for u in users if u['username']=='viewer')
    cookie=internal.cookies.get('session')
    sign_in(internal,'viewer','viewer-password-123')
    viewer_cookie=internal.cookies.get('session')
    internal.cookies.set('session',cookie)
    assert internal.patch(f'/api/v1/admin/users/{viewer["id"]}',headers=CSRF,json={'active':False}).status_code==200
    internal.cookies.set('session',viewer_cookie)
    assert internal.get('/api/v1/calls').status_code==401


def cdr(**overrides):
    return {**{'call_id':'1700000000.123','direction':'inbound','client_number':'+12025550101',
        'did_number':'+12025550199','status':'answered','agent_name':'Agent One','department_name':'Support',
        'recording_url':'https://recording.example/?token=DO-NOT-EXPOSE','call_flow':[
            {'type':'init','time':1700000000,'value':'1700000000.123'},
            {'type':'IVR','name':'Welcome','time':1700000002},
            {'type':'hangup','time':1700000100}]},**overrides}


def test_cdr_projection_is_conservative_and_does_not_fabricate_attempts():
    call=project_record(cdr())
    assert call['status']=='ANSWERED' and not call['synthetic']
    assert call['legs']==[] and call['ring_attempts'] is None and call['missed_attempts'] is None
    assert call['answered_at'] is None and call['first_response_seconds'] is None
    assert 'DO-NOT-EXPOSE' not in str(call)


def test_unknown_caller_does_not_drop_an_identified_customer_call(internal):
    with internal.app.state.sessions.begin() as db:
        assert store_record(db,cdr(client_number='anonymous'))
        root=db.scalar(select(Call))
        assert root.caller_e164 is None and root.final_status=='ANSWERED'
        assert any('Caller unavailable' in warning for warning in root.projection['warnings'])


def test_cdr_revisions_keep_history_and_recording_tokens_are_not_stored(internal):
    with internal.app.state.sessions.begin() as db:
        assert store_record(db,cdr())
        assert not store_record(db,cdr())
        assert store_record(db,cdr(status='missed',call_flow=[{'type':'hangup','time':1700000110}]))
        assert db.scalar(select(func.count()).select_from(Call))==1
        assert db.scalar(select(func.count()).select_from(CallEvent))==2
        assert all('DO-NOT-EXPOSE' not in str(row.payload) for row in db.scalars(select(CallEvent)))
        assert len(db.scalar(select(Call)).projection['events'])==4


def test_provider_retry_is_bounded_and_error_does_not_echo_body():
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(429,json={'error':'SECRET-CREDENTIAL'},headers={'Retry-After':'9999'})
    sleeps=[]
    client=ReadOnlyTransport('https://api.acefone.in',{},httpx.MockTransport(handler),interval=0,sleep=sleeps.append)
    with pytest.raises(ProviderError) as exc:client.request('GET','/v1/call/records')
    assert len(calls)==3 and max(sleeps)<=30
    assert 'SECRET-CREDENTIAL' not in str(exc.value)
    client.close()


def test_leadsquared_enumeration_uses_documented_contract():
    def handler(request):
        import json
        assert request.method=='POST' and request.url.path=='/v2/LeadManagement.svc/Leads.Get'
        assert json.loads(request.content)['Paging']=={'PageIndex':2,'PageSize':100}
        assert not request.url.query
        return httpx.Response(200,json=[])
    client=LiveLeadSquaredClient({'LEADSQUARED_API_HOST':'https://api-in21.leadsquared.com/v2/',
        'LEADSQUARED_ACCESS_KEY':'test','LEADSQUARED_SECRET_KEY':'test'},transport=httpx.MockTransport(handler),interval=0)
    assert client.page(2)==[]
    client.close()


def test_sqlite_backup_restore(tmp_path):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    from backup_internal import backup
    source=tmp_path/'internal.db'
    with sqlite3.connect(source) as db:
        db.execute('create table verification (id integer primary key, value text)')
        db.execute("insert into verification values (1,'restore-ok')")
    target=backup(source,tmp_path/'backup/restored.db')
    with sqlite3.connect(target) as restored:
        assert restored.execute('select value from verification').fetchone()[0]=='restore-ok'
        assert restored.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert target.stat().st_mode & 0o077==0


def test_network_install_requires_https(tmp_path):
    with pytest.raises(ValueError,match='HTTPS'):
        Settings(mode='internal',database_url='sqlite:///internal.db',origin='http://staff.example.com').validate()


def test_live_crm_keeps_all_duplicate_candidates_and_all_phone_numbers(internal,monkeypatch):
    from app import live_sync
    from app.db import LeadMatch,LeadPhone
    class FakeCRM:
        def __init__(self,*args,**kwargs):pass
        def page(self,index,size):
            return [dict(ProspectID=f'lead-{i}',FirstName='Test',LastName=str(i),Phone='+12025550101',
                         Mobile='+12025550102',CreatedOn='2026-10-01 01:00:00',OwnerId='owner',ProspectStage='New',Source='Test')
                    for i in range(2)]
        def close(self):pass
    monkeypatch.setattr(live_sync,'LiveLeadSquaredClient',FakeCRM)
    with internal.app.state.sessions.begin() as db:store_record(db,cdr())
    worker=live_sync.LiveSync(internal.app.state.settings,internal.app.state.sessions)
    worker.crm({})
    with internal.app.state.sessions() as db:
        root=db.scalar(select(Call))
        assert root.projection['crm']['status']=='MULTIPLE_MATCHES'
        assert len(root.projection['crm']['candidates'])==2
        assert db.scalar(select(func.count()).select_from(LeadPhone))==4
        assert db.scalar(select(func.count()).select_from(LeadMatch))==2


def test_effective_department_mapping_respects_call_date(internal):
    from app.db import DepartmentMapping
    from app.mappings import apply_mappings
    from datetime import UTC,datetime
    with internal.app.state.sessions.begin() as db:
        store_record(db,cdr(department_name=None))
        db.add(DepartmentMapping(source_type='DID',source_value='+12025550199',department='Admissions',
                                effective_from=datetime(2020,1,1,tzinfo=UTC),effective_to=None))
        db.flush();apply_mappings(db)
        root=db.scalar(select(Call))
        assert root.projection['primary_department']=='Admissions'
        mapping=db.scalar(select(DepartmentMapping))
        mapping.effective_from=datetime(2030,1,1,tzinfo=UTC)
        db.flush();apply_mappings(db)
        assert root.projection['primary_department'] is None


def test_large_crm_scan_resumes_without_promoting_partial_index(internal,monkeypatch):
    from app import live_sync
    from app.db import CRMScanRow,IntegrationState,Lead,LeadPhone
    requested=[]
    class FakeLargeCRM:
        def __init__(self,*args,**kwargs):pass
        def page(self,index,size):
            requested.append(index)
            if index>20:return []
            return [dict(ProspectID=f'lead-{index:03}-{i:04}',FirstName='Test',LastName='Lead',Phone='+12025550101',
                         CreatedOn='2026-10-01 01:00:00',OwnerId='owner',ProspectStage='New',Source='Test') for i in range(1000)]
        def close(self):pass
    monkeypatch.setattr(live_sync,'LiveLeadSquaredClient',FakeLargeCRM)
    worker=live_sync.LiveSync(internal.app.state.settings,internal.app.state.sessions)
    worker.crm({})
    with internal.app.state.sessions() as db:
        assert db.get(IntegrationState,'leadsquared').status=='INDEXING'
        assert db.scalar(select(func.count()).select_from(CRMScanRow))==20000
        assert db.scalar(select(func.count()).select_from(Lead))==0
    # A new worker represents a process restart. It resumes at the saved page.
    worker=live_sync.LiveSync(internal.app.state.settings,internal.app.state.sessions)
    worker.crm({})
    assert requested==list(range(1,22))
    with internal.app.state.sessions() as db:
        assert db.get(IntegrationState,'leadsquared').status=='HEALTHY'
        assert db.scalar(select(func.count()).select_from(Lead))==20000
        assert db.scalar(select(func.count()).select_from(LeadPhone))==20000
