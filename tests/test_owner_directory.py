from datetime import UTC,datetime,timedelta
import httpx
from app.owner_directory import refresh_owner_directory,owner_names,resolve_owner_name
from app.provider_clients import LiveLeadSquaredClient,ProviderError
from test_internal import internal

OWNER='11111111-2222-3333-4444-555555555555'

def test_user_api_uses_documented_get_and_header_credentials():
    def handler(request):
        assert request.method=='GET' and request.url.path=='/v2/UserManagement.svc/Users.Get'
        assert not request.url.query and request.headers['x-LSQ-AccessKey']=='test'
        return httpx.Response(200,json=[{'ID':OWNER,'FirstName':'Owner','LastName':'Name','StatusCode':1}])
    client=LiveLeadSquaredClient({'LEADSQUARED_API_HOST':'https://api-in21.leadsquared.com',
        'LEADSQUARED_ACCESS_KEY':'test','LEADSQUARED_SECRET_KEY':'test'},transport=httpx.MockTransport(handler),interval=0)
    assert client.users()[0]['ID']==OWNER
    client.close()


def test_directory_cache_and_failure_preserve_names(internal):
    calls=[]
    class Fake:
        def __init__(self,credentials):pass
        def users(self):calls.append(1);return [{'ID':OWNER,'FirstName':'Owner','LastName':'Name','EmailAddress':'not-stored@example.com'}]
        def close(self):pass
    sessions=internal.app.state.sessions;clock=datetime(2026,10,29,tzinfo=UTC)
    assert refresh_owner_directory(sessions,{},client_factory=Fake,clock=clock)['status']=='UPDATED'
    assert refresh_owner_directory(sessions,{},client_factory=Fake,clock=clock+timedelta(minutes=20))['status']=='CACHED'
    assert len(calls)==1
    class Broken(Fake):
        def users(self):raise ProviderError('secret response must not be retained')
    assert refresh_owner_directory(sessions,{},client_factory=Broken,clock=clock+timedelta(hours=2))['status']=='ERROR'
    with sessions() as db:
        names=owner_names(db)
        assert names=={OWNER:'Owner Name'}
        assert resolve_owner_name(OWNER.upper(),names)=='Owner Name'
        assert resolve_owner_name('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',names) is None
        assert resolve_owner_name('Fixture Owner',names)=='Fixture Owner'
    assert refresh_owner_directory(sessions,{},client_factory=Broken,clock=clock+timedelta(hours=2,minutes=1))['status']=='RETRY_LATER'


def test_call_details_and_journey_resolve_current_owner_name(internal):
    from sqlalchemy import select
    from app.db import Call,IntegrationState,Lead
    from app.cdr import store_record
    from app.crm import enrich
    from types import SimpleNamespace
    from test_internal import cdr,sign_in
    candidate=dict(id='lead-owner',display_name='Test lead',current_stage='New',
        current_owner=OWNER,created_at='2026-01-01T00:00:00Z',source='Test',phones=['+12025550101'])
    with internal.app.state.sessions.begin() as db:
        store_record(db,cdr());call=db.scalar(select(Call));call_id=call.id
        enrich(db,call,SimpleNamespace(lookup=lambda _: [candidate]),force=True)
        db.add(IntegrationState(provider='leadsquared-users',status='HEALTHY',details={'owners':{OWNER:'Owner Name'}}))
    sign_in(internal,'viewer','viewer-password-123')
    for suffix in ['', '/journey','/crm']:
        response=internal.get('/api/v1/calls/'+call_id+suffix)
        assert response.status_code==200
        crm=response.json() if suffix=='/crm' else response.json()['crm']
        assert crm['candidates'][0]['current_owner_name']=='Owner Name'
        assert crm['candidates'][0]['display_name']=='Restricted lead'
    with internal.app.state.sessions.begin() as db:
        db.get(Lead,'lead-owner').current_owner='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    # Missing names remain unavailable; never label an ID as a name.
    result=internal.get('/api/v1/calls/'+call_id+'/journey').json()
    assert result['crm']['candidates'][0]['current_owner_name'] is None
