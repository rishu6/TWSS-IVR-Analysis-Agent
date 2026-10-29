from datetime import datetime,UTC
from types import SimpleNamespace
from sqlalchemy import select
from app.cdr import store_record
from app.crm import enrich
from app.crm_analytics import analytics
from app.db import Call
from test_internal import internal,sign_in,cdr


def lead(id='old',created='2026-01-01T00:00:00Z',stage='Contacted'):
    return dict(id=id,display_name='Fictional Private Lead',created_at=created,current_stage=stage,
        current_owner='Owner',source='Fixture',phones=['+12025550101'])


def add(db,id,phone='+12025550101',department=True,status='answered',leads=None,error=False,day=15):
    at=int(datetime(2026,10,day,4,30,tzinfo=UTC).timestamp())
    flow=[{'type':'init','time':at},{'type':'IVR','name':'Menu','time':at+1}]
    if department:flow.append({'type':'Department','name':'Admissions','time':at+2})
    flow.append({'type':'hangup','time':at+60})
    store_record(db,cdr(call_id=id,client_number=phone,status=status,department_name=None,
        date=f'2026-10-{day}',time='10:00:00',call_flow=flow))
    call=db.scalar(select(Call).where(Call.provider_call_id==id))
    if leads is not None:enrich(db,call,SimpleNamespace(lookup=lambda phone:leads),force=True)
    if error:call.projection={**call.projection,'crm':{'status':'ERROR','candidates':[],'stale':True}}
    return call


def test_unique_callers_repeat_calls_creation_date_and_current_stage(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'one',leads=[lead()]);add(db,'repeat',leads=[{**lead(stage='Qualified'),'current_owner':'Updated Owner'}])
        add(db,'new',phone='+12025550102',leads=[lead('new','2026-10-16T00:00:00Z')])
        add(db,'missing',phone='+12025550103',leads=[])
        add(db,'pending',phone='+12025550104',error=True)
        add(db,'no-department',phone='+12025550105',department=False,leads=[])
        summary,rows=analytics(db,db.scalars(select(Call)).all(),'Admin')
        assert summary['total_calls']==5 and summary['unique_callers']==4
        assert summary['matched_callers']==2 and summary['matched_calls']==3
        assert summary['repeat_calls']==1 and summary['no_match_callers']==1
        assert summary['unresolved_callers']==1
        assert summary['existing_before_call']==1 and summary['created_after_call']==1
        old=next(row for row in rows if row['call_count']==2)
        assert old['candidates'][0]['current_owner']=='Updated Owner'
        assert old['candidates'][0]['current_stage']=='Qualified'  # latest saved Lead, not old call snapshot
        assert old['candidates'][0]['created_at'].startswith('2026-01-01')


def test_duplicates_preserved_and_unknown_numbers_never_grouped(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'multiple',leads=[lead(),lead('another','2026-10-16T00:00:00Z')])
        add(db,'unknown1',phone='anonymous');add(db,'unknown2',phone='anonymous')
        summary,rows=analytics(db,db.scalars(select(Call)).all(),'Viewer')
        assert summary['unique_callers']==1 and summary['unknown_caller_calls']==2
        assert summary['multiple_match_callers']==1 and summary['matched_callers']==1
        assert len(rows)==3
        assert '+1202555' not in str(rows) and 'Fictional Private Lead' not in str(rows)
        candidate=next(row for row in rows if row['candidates'])
        assert len(candidate['candidates'])==2
        assert summary['existing_before_call']==1


def test_report_combines_date_department_status_and_paginates_callers(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'old',leads=[lead()]);add(db,'repeat',leads=[lead()])
        add(db,'different',phone='+12025550102',leads=[])
        add(db,'otherday',day=16,leads=[]);add(db,'missed',status='missed',leads=[])
        add(db,'ivr',department=False,leads=[])
    sign_in(internal,'viewer','viewer-password-123')
    params={'start':'2026-10-14T18:30:00Z','end':'2026-10-15T18:30:00Z',
        'department':'Admissions','outcome':'ANSWERED','page_size':1}
    response=internal.get('/api/v1/reports/leadsquared',params=params)
    assert response.status_code==200
    data=response.json()
    assert data['summary']['total_calls']==3 and data['summary']['unique_callers']==2
    assert len(data['items'])==1 and data['next_page']==2
    params['page']=2
    assert len(internal.get('/api/v1/reports/leadsquared',params=params).json()['items'])==1
    assert '+1202555' not in response.text and 'Fictional Private Lead' not in response.text
    assert internal.get('/api/v1/reports/leadsquared?start=2027-01-01T00:00:00Z').json()['summary']['total_calls']==0


def test_department_toggle_and_unauthenticated_access(internal):
    assert internal.get('/api/v1/reports/leadsquared').status_code==401
    with internal.app.state.sessions.begin() as db:add(db,'ivr',department=False,leads=[])
    sign_in(internal,'viewer','viewer-password-123')
    assert internal.get('/api/v1/reports/leadsquared').json()['summary']['total_calls']==0
    assert internal.get('/api/v1/reports/leadsquared?department_selected=false').json()['summary']['total_calls']==1


def test_ls_rankings_use_full_report_selection_and_exclude_support(internal):
    with internal.app.state.sessions.begin() as db:
        add(db,'one',leads=[lead()]);add(db,'two',phone='+12025550102',leads=[])
        support=add(db,'support',phone='+12025550103',leads=[])
        support.projection={**support.projection,'departments':['Admissions','Support']}
        add(db,'ivr',department=False,leads=[])
    sign_in(internal,'viewer','viewer-password-123')
    data=internal.get('/api/v1/reports/leadsquared?page_size=1&outcome=ANSWERED').json()
    assert data['summary']['total_calls']==3
    assert len(data['items'])==1
    ranked={a['agent']:a for a in data['ranking_items']}
    assert ranked['Agent One']['answered_call_count']==2  # all report rows, not one visible page
    with_ivr=internal.get('/api/v1/reports/leadsquared?department_selected=false&outcome=ANSWERED').json()
    assert next(a for a in with_ivr['ranking_items'] if a['agent']=='Agent One')['answered_call_count']==3
    assert internal.get('/api/v1/reports/leadsquared?outcome=MISSED').json()['ranking_items']==[]


def test_owner_id_resolves_to_name_without_changing_stored_id(internal):
    from app.db import IntegrationState
    owner='11111111-2222-3333-4444-555555555555'
    with internal.app.state.sessions.begin() as db:
        add(db,'owner-test',leads=[{**lead(),'current_owner':owner}])
        db.add(IntegrationState(provider='leadsquared-users',status='HEALTHY',details={'owners':{owner:'Verified Owner Name'}}))
    sign_in(internal,'viewer','viewer-password-123')
    response=internal.get('/api/v1/reports/leadsquared')
    assert response.status_code==200
    candidate=response.json()['items'][0]['candidates'][0]
    assert candidate['current_owner_name']=='Verified Owner Name'
    assert candidate['current_owner']==owner
