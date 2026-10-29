from datetime import UTC, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import exists, or_, select

from .db import Call, CallLeg, CallParticipant, Lead, LeadMatch
from .domain import timestamp
from .agent_outcomes import outcome_report


def filtered_query(q=None, department=None, agent=None, did=None, outcome=None, stage=None, owner=None,
                   start=None, end=None, direction=None):
    stmt = select(Call)
    if q:
        escaped = q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        term = f'%{escaped}%'
        stmt = stmt.where(or_(Call.id.ilike(term, escape='\\'), Call.provider_call_id.ilike(term,escape='\\'), Call.caller_e164.ilike(term, escape='\\'),
                              Call.dialed_did.ilike(term, escape='\\'), Call.projection['answering_agent'].as_string().ilike(term,escape='\\'), exists(select(CallLeg.id).where(
                                  CallLeg.call_id == Call.id, CallLeg.agent.ilike(term, escape='\\'))),
                              exists(select(CallParticipant.id).where(CallParticipant.call_id==Call.id,CallParticipant.agent_name.ilike(term,escape='\\')))))
    if department:
        stmt = stmt.where(Call.projection['primary_department'].as_string() == department)
    if agent:
        stmt = stmt.where(or_(Call.projection['answering_agent'].as_string()==agent,
                             exists(select(CallLeg.id).where(CallLeg.call_id == Call.id, CallLeg.agent == agent)),
                             exists(select(CallParticipant.id).where(CallParticipant.call_id==Call.id,CallParticipant.agent_name==agent))))
    if did:
        stmt = stmt.where(Call.dialed_did == did)
    if outcome:
        stmt = stmt.where(Call.final_status == outcome)
    if direction:
        stmt = stmt.where(Call.direction == direction)
    if start:
        stmt = stmt.where(Call.started_at >= start)
    if end:
        stmt = stmt.where(Call.started_at < end)
    if stage or owner:
        match = select(LeadMatch.call_id).join(Lead, LeadMatch.lead_id == Lead.id).where(LeadMatch.call_id == Call.id)
        if stage:
            match = match.where(Lead.current_stage == stage)
        if owner:
            match = match.where(Lead.current_owner == owner)
        stmt = stmt.where(exists(match))
    return stmt.order_by(Call.started_at.desc(), Call.id)


def mask_phone(value):
    return f'••••••{value[-4:]}' if value else None


def present(call, role, journey=False, db=None):
    data = {**call.projection}
    data.pop('events', None)
    data['event_count']=len(call.projection.get('events',[]))
    data['crm'] = dict(data.get('crm', {'status': 'PENDING', 'candidates': [], 'snapshot_source': 'current only'}))
    if db is not None:
        from .owner_directory import owner_names,resolve_owner_name
        names=owner_names(db)
        candidates=[]
        for lead in data['crm'].get('candidates',[]):
            current=db.get(Lead,lead['id'])
            owner=current.current_owner if current else lead.get('current_owner')
            candidates.append({**lead,'current_owner_name':resolve_owner_name(owner,names)})
        data['crm']['candidates']=candidates
    if role == 'Viewer':
        data['caller'] = mask_phone(data['caller'])
        data['did'] = mask_phone(data['did'])
        data['crm']['candidates'] = [{**lead, 'display_name': 'Restricted lead'} for lead in data['crm'].get('candidates', [])]
        data['transfers'] = [{**transfer, 'caller': data['caller'], 'did': data['did']}
                             for transfer in data['transfers']]
        for field in ('participants','reported_missed_agents'):
            data[field]=[{**p,'agent_number':mask_phone(p.get('agent_number'))} for p in data.get(field,[])]
        if data.get('provider_dtmf_input') and len(data['provider_dtmf_input'])>4:
            data['provider_dtmf_input']=mask_phone(data['provider_dtmf_input'])
    if journey:
        data['events'] = [{**event, 'caller': data['caller'], 'did': data['did'],
                          **({'agent_number':mask_phone(event.get('agent_number'))} if role=='Viewer' else {})}
                          for event in call.projection['events']]
    return data


def exclude_department_calls(calls,department):
    excluded=department.strip().casefold()
    return [c for c in calls if not any(str(d).strip().casefold()==excluded for d in
        [c.projection.get('primary_department'),*c.projection.get('departments',[])])]


def has_department_flow(call):
    """Require recorded department routing; a DID/reporting label alone is insufficient.

    CDR routing does not prove which keypad key selected the department.
    """
    events=call.get('events',[])
    if call.get('synthetic'):
        return any(e.get('department') and e.get('type') in ('QUEUED','RING','ANSWER') for e in events)
    return any(e.get('type')=='Department' and str(e.get('node') or '').strip() for e in events)


def overview(calls):
    inbound = [c.projection for c in calls if c.direction == 'inbound']
    statuses = {s: sum(c['status'] == s for c in inbound) for s in
                ('ANSWERED', 'MISSED', 'IVR_ONLY', 'ABANDONED', 'IN_PROGRESS', 'UNKNOWN')}
    responses = [c['first_response_seconds'] for c in inbound if c['first_response_seconds'] is not None]
    durations = [c['duration_seconds'] for c in inbound if c['duration_seconds'] is not None]
    customer_missed=sum(c['status']=='MISSED' and has_department_flow(c) for c in inbound)
    hours, dids = {}, {}
    for call in inbound:
        if call['started_at']:
            hour = (timestamp(call['started_at']).astimezone(ZoneInfo('Asia/Kolkata'))
                    .replace(minute=0, second=0, microsecond=0).astimezone(UTC).isoformat())
            group = hours.setdefault(hour, {'at': hour, 'total': 0, 'answered': 0, 'missed': 0, 'customer_missed': 0})
            group['total'] += 1
            group['answered'] += call['status'] == 'ANSWERED'
            group['missed'] += call['status'] == 'MISSED'
            group['customer_missed'] += call['status']=='MISSED' and has_department_flow(call)
        dids[call['did']] = dids.get(call['did'], 0) + 1
    return {'unique_callers':len({c.caller_e164 for c in calls if c.direction=='inbound' and c.caller_e164}), 'total': len(inbound), **statuses, 'customer_missed':customer_missed,
            'missed_without_department':statuses['MISSED']-customer_missed, 'answer_rate': statuses['ANSWERED'] / len(inbound) if inbound else None,
            'average_response_seconds': sum(responses) / len(responses) if responses else None,
            'response_sample_size': len(responses),
            'average_duration_seconds': sum(durations) / len(durations) if durations else None,
            'duration_sample_size': len(durations), 'hourly': sorted(hours.values(), key=lambda h: h['at']),
            'by_did': [{'did': did, 'total': total} for did, total in dids.items()],
            'missing_attempt_coverage': sum(not c['attempts_available'] for c in inbound),
            'definitions': {'answer_rate': 'Answered inbound logical calls / all filtered inbound logical calls',
                            'missed': 'All inbound calls with a provider missed outcome, including calls without department routing; not agent attempts',
                            'customer_missed': 'Missed inbound logical calls with a named Department event in the recorded flow. Excludes calls with only a reporting/DID department label. Counts calls, not unique phone numbers. Department routing is the available evidence; exact keypad selection is not verified.',
                            'response': 'Mean first explicit answer minus inbound start, only where both are known',
                            'duration': 'Mean end minus inbound start for completed inbound calls with valid timestamps'}}


def agent_report(calls):
    groups = {}
    for row in calls:
        call = row.projection
        if row.provider=='acefone' and call.get('answering_agent') and call['status']=='ANSWERED':
            name=call['answering_agent']
            group=groups.setdefault(name,dict(agent=name,ring_attempts=None,missed_attempts=None,answered_legs=None,
                answered_calls=0,known_talk_seconds=None,incomplete_talk_legs=0,response_samples=[],transfers=None,
                partial_ring_coverage=True,metric_scope='final_answer_agent'))
            group['answered_calls']+=1
        for leg in call['legs']:
            if not leg['agent']:
                continue
            group = groups.setdefault(leg['agent'], dict(agent=leg['agent'], ring_attempts=0, missed_attempts=0,
                answered_legs=0, known_talk_seconds=0, incomplete_talk_legs=0, response_samples=[], transfers=0,
                partial_ring_coverage=False))
            if not call['attempts_available']:
                group['partial_ring_coverage'] = True
            group['ring_attempts'] += leg['ring_at'] is not None
            group['missed_attempts'] += leg['disposition'] == 'NO_ANSWER'
            group['answered_legs'] += leg['disposition'] == 'ANSWERED'
            group['known_talk_seconds'] += leg['talk_seconds'] or 0
            group['incomplete_talk_legs'] += leg['answer_at'] is not None and leg['talk_seconds'] is None
            if leg['response_seconds'] is not None:
                group['response_samples'].append(leg['response_seconds'])
            group['transfers'] += sum(t['source_leg_id'] == leg['id'] for t in call['transfers'])
    for group in groups.values():
        samples = group.pop('response_samples')
        group['average_response_seconds'] = sum(samples) / len(samples) if samples else None
        if group['partial_ring_coverage']:
            group['ring_attempts'] = group['missed_attempts'] = None
    for name,summary in outcome_report(calls).items():
        group=groups.setdefault(name,dict(agent=name,ring_attempts=None,missed_attempts=None,
            answered_legs=None,known_talk_seconds=None,incomplete_talk_legs=0,
            average_response_seconds=None,transfers=None,partial_ring_coverage=True))
        group.update(summary)
    return sorted(groups.values(), key=lambda g: g['agent'])


def department_report(calls):
    groups = {}
    for row in calls:
        if row.direction != 'inbound':
            continue
        call = row.projection
        for department in call['departments']:
            group = groups.setdefault(department, dict(department=department, primary_calls=0, involved_calls=0, answered_primary=0, missed_primary=0))
            group['involved_calls'] += 1
            if department == call['primary_department']:
                group['primary_calls'] += 1
                group['answered_primary'] += call['status'] == 'ANSWERED'
                group['missed_primary'] += call['status'] == 'MISSED'
    return sorted(groups.values(), key=lambda g: g['department'])


def recovery_candidates(calls, hours):
    used, results = set(), []
    ordered = sorted([c.projection for c in calls if c.projection['started_at']], key=lambda c: (c['started_at'], c['id']))
    for missed in ordered:
        if missed['direction'] != 'inbound' or missed['status'] != 'MISSED' or not missed['ended_at']:
            continue
        after = timestamp(missed['ended_at'])
        if not missed['caller'] or not missed['did']:
            results.append({'call_id':missed['id'],'caller':missed['caller'],'missed_at':missed['ended_at'],
                'status':'RECOVERY_UNKNOWN','recovery_call_id':None,'window_hours':hours,
                'evidence':'Caller or DID unavailable; no recovery association inferred'})
            continue
        match = next((c for c in ordered if c['id'] not in used and c['id'] != missed['id'] and
                      c['caller'] == missed['caller'] and c['did'] == missed['did'] and c['answered_at'] and
                      timestamp(c['started_at']) >= after and
                      after < timestamp(c['answered_at']) <= after + timedelta(hours=hours)), None)
        if match:
            used.add(match['id'])
        results.append({'call_id': missed['id'], 'caller': missed['caller'], 'missed_at': missed['ended_at'],
                        'status': 'RECOVERY_CANDIDATE' if match else 'UNRECOVERED',
                        'recovery_call_id': match['id'] if match else None, 'window_hours': hours,
                        'evidence': 'Phone + DID + subsequent answer; shared numbers may cause false positives'})
    return results
