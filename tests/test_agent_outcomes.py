from types import SimpleNamespace

from app.agent_outcomes import outcome_report
from app.cdr import project_record,store_record
from test_history_and_flow import agent_flow
from test_internal import internal,sign_in


def report(record):
    return outcome_report([SimpleNamespace(projection=project_record(record))])


def test_report_includes_missed_only_agents_and_answer_position():
    result=report(agent_flow())
    assert result['First Agent']['missed_call_count']==1
    assert result['First Agent']['answered_call_count']==0
    assert result['First Agent']['missed_by_attempt']=={'unknown':1}
    assert result['Final Agent']['answered_call_count']==1
    assert result['Final Agent']['answered_by_attempt']=={'2':1}


def test_repeat_calls_count_separately_but_duplicate_summary_and_events_do_not():
    record=agent_flow()
    record['missed_agents']*=2
    record['call_flow']+=record['call_flow'][2:5]
    projection=project_record(record)
    result=outcome_report([SimpleNamespace(projection=projection)]*2)
    assert result['First Agent']['missed_call_count']==2
    assert result['Final Agent']['answered_by_attempt']=={'2':2}


def test_multiple_dials_for_answerer_leave_attempt_unknown():
    record=agent_flow()
    record['call_flow'].append({'type':'Agent','id':'agent-2','name':'Final Agent','dialst':'Dialed','time':1700000011})
    assert report(record)['Final Agent']['answered_by_attempt']=={'unknown':1}


def test_simultaneous_dials_have_no_fabricated_attempt_order():
    record=agent_flow()
    record['call_flow'][3]['time']=record['call_flow'][2]['time']
    assert report(record)['Final Agent']['answered_by_attempt']=={'unknown':1}


def test_all_answerers_count_once_even_with_missed_summary_and_cdr_fallback():
    record=agent_flow()
    record['missed_agents'].append({'name':'Final Agent','number':'+12025550103'})
    record['call_flow'].append({'type':'Agent','name':'Another Agent','dialst':'Answered','time':1700000050})
    result=report(record)
    assert result['Final Agent']['answered_call_count']==1
    assert result['Final Agent']['missed_call_count']==1
    assert result['Another Agent']['answered_by_attempt']=={'unknown':1}
    record['call_flow']=[];record['missed_agents']=[];record['agent_name']='CDR Answerer'
    assert report(record)['CDR Answerer']['answered_by_attempt']=={'unknown':1}


def test_report_endpoint_obeys_status_and_department_filters(internal):
    with internal.app.state.sessions.begin() as db:
        store_record(db,agent_flow())
        store_record(db,{**agent_flow(),'call_id':'another','status':'missed','call_flow':[],'department_name':'Support'})
    sign_in(internal,'viewer','viewer-password-123')
    response=internal.get('/api/v1/reports/agents?department=Admissions&outcome=ANSWERED')
    assert response.status_code==200
    rows={r['agent']:r for r in response.json()['items']}
    assert rows['First Agent']['missed_call_count']==1
    assert rows['Final Agent']['answered_by_attempt']=={'2':1}
    assert internal.get('/api/v1/reports/agents?department=Missing').json()['items']==[]


def test_synthetic_explicit_no_answer_leg_has_a_known_position():
    call={'synthetic':True,'status':'MISSED','events':[
        {'event_id':'1','type':'RING','agent':'Demo Agent','leg_id':'leg1','at':'2026-01-01T00:00:00Z'},
        {'event_id':'2','type':'NO_ANSWER','agent':'Demo Agent','leg_id':'leg1','at':'2026-01-01T00:00:10Z'}]}
    assert outcome_report([SimpleNamespace(projection=call)])['Demo Agent']['missed_by_attempt']=={'1':1}


def test_agent_ratios_use_unique_involved_calls_not_sum_of_overlapping_outcomes():
    both=agent_flow()
    both['missed_agents'].append({'name':'Final Agent','number':'+12025550103'})
    projection=project_record(both)
    dial_only=project_record({**agent_flow(),'call_id':'dial-only','status':'missed','missed_agents':[],
        'call_flow':[e for e in agent_flow()['call_flow'] if e.get('dialst')!='Answered']})
    result=outcome_report([SimpleNamespace(projection=p) for p in (projection,dial_only)])
    agent=result['Final Agent']
    assert agent['total_call_count']==2
    assert agent['answered_call_count']==agent['missed_call_count']==1
    assert agent['answered_call_ratio']==agent['missed_call_ratio']==0.5
    overlapping=outcome_report([SimpleNamespace(projection=projection)])['Final Agent']
    assert overlapping['total_call_count']==1
    assert overlapping['answered_call_ratio']==overlapping['missed_call_ratio']==1


def test_empty_agent_report_has_no_ratios_and_dial_only_has_zero_outcomes():
    assert outcome_report([])=={}
    record={**agent_flow(),'status':'missed','missed_agents':[],
        'call_flow':[e for e in agent_flow()['call_flow'] if e.get('dialst')!='Answered']}
    result=report(record)
    assert result['Final Agent']['total_call_count']==1
    assert result['Final Agent']['answered_call_ratio']==result['Final Agent']['missed_call_ratio']==0


def test_ranking_support_exclusion_is_per_call_before_aggregation(internal):
    selected=agent_flow()
    # First department Admissions, later department Support: exclude the entire call.
    with internal.app.state.sessions.begin() as db:
        store_record(db,selected)
        admissions={**agent_flow(),'call_id':'admissions-only','call_flow':[
            e for e in agent_flow()['call_flow'] if e.get('name')!='Support']}
        store_record(db,admissions)
    sign_in(internal,'viewer','viewer-password-123')
    response=internal.get('/api/v1/reports/agents?ranking_exclude_department=Support')
    assert response.status_code==200
    data=response.json()
    all_agents={a['agent']:a for a in data['items']}
    ranked={a['agent']:a for a in data['ranking_items']}
    assert all_agents['Final Agent']['answered_call_count']==2
    assert ranked['Final Agent']['answered_call_count']==1
    assert ranked['First Agent']['missed_call_count']==1
    assert internal.get('/api/v1/reports/agents?department=Support&ranking_exclude_department=Support').json()['ranking_items']==[]
    assert internal.get('/api/v1/reports/agents?ranking_exclude_department=%20sUpPoRt%20').json()['ranking_items']==data['ranking_items']
