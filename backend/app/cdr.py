"""CDR projection uses documented fields only; no fabricated per-agent legs."""
import hashlib
import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from .crm import normalize_phone
from .db import Call, CallEvent, CallParticipant, IntegrationEvent, now
from sqlalchemy import delete
from .domain import seconds


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def restricted_payload(value):
    if isinstance(value,dict):
        return {k:('[REDACTED]' if any(word in k.lower() for word in ('url','token','secret','password','authorization'))
                   else restricted_payload(v)) for k,v in value.items()}
    if isinstance(value,list):return [restricted_payload(v) for v in value]
    return value


def epoch(value):
    try:
        number = float(value)
        return datetime.fromtimestamp(number, UTC).isoformat() if number > 0 else None
    except (TypeError,ValueError,OverflowError,OSError):
        return None


def agent_number(entry):
    value=entry.get('num') or entry.get('number')
    if value is None:return None
    try:return normalize_phone(str(value))
    except ValueError:return str(value)[:40]


def flow_participants(root,flow,missed):
    participants={}
    def participant(entry):
        number=agent_number(entry)
        name=str(entry.get('name') or '')[:120] or None
        provider_id=str(entry['id'])[:120] if entry.get('id') is not None else None
        key=number or ('id:'+provider_id if provider_id else 'name:'+name if name else None)
        if not key:return None
        row=participants.setdefault(key,{'id':hashlib.sha256((root+key).encode()).hexdigest(),
            'agent_name':name,'agent_number':number,'provider_agent_id':provider_id,
            'dialed_at':[],'answered_at':[],'reported_missed':False,'missed_at':None})
        row['agent_name']=row['agent_name'] or name
        row['provider_agent_id']=row['provider_agent_id'] or provider_id
        return row
    for entry in flow:
        if not isinstance(entry,dict) or entry.get('type')!='Agent':continue
        row=participant(entry)
        at=epoch(entry.get('time'))
        if row and at and entry.get('dialst') in ('Dialed','Answered'):
            key='dialed_at' if entry['dialst']=='Dialed' else 'answered_at'
            if at not in row[key]:row[key].append(at)
    for entry in missed:
        if not isinstance(entry,dict):continue
        row=participant(entry)
        if row:row['reported_missed']=True
    return list(participants.values())


def project_record(record, source_timezone='Asia/Kolkata'):
    provider_id = str(record.get('call_id') or '')
    if not provider_id or record.get('direction') not in ('inbound','outbound'):
        raise ValueError('CDR root ID or direction missing')
    root = 'acefone-'+hashlib.sha256(provider_id.encode()).hexdigest()[:32]
    warnings = ['Per-agent ring coverage and transfer leg linkage are unavailable from the verified CDR contract']
    def phone(value,field):
        try:return normalize_phone(value or '')
        except ValueError:
            warnings.append(field+' unavailable: provider phone could not be normalized')
            return None
    caller,did=phone(record.get('client_number'),'Caller'),phone(record.get('did_number'),'DID')
    flow = record.get('call_flow') or []
    if not isinstance(flow,list):
        raise ValueError('Invalid CDR call flow')
    events, starts, ends, answers = [], [], [], []
    departments=[]
    for entry in flow:
        if not isinstance(entry,dict):
            continue
        at = epoch(entry.get('time'))
        if not at:
            continue
        kind = str(entry.get('type') or 'PROVIDER_EVENT')
        if kind.lower() == 'init': starts.append(at)
        if kind.lower() == 'hangup': ends.append(at)
        if kind == 'Agent' and entry.get('dialst') == 'Answered': answers.append(at)
        if kind=='Department' and entry.get('name') and entry['name'] not in departments:
            departments.append(str(entry['name'])[:120])
        # Only expose documented non-secret labels, never raw payload/recording URLs.
        event = {'event_id':hashlib.sha256((root+canonical(entry)).encode()).hexdigest(),
                 'type':kind,'at':at,'node':(str(entry.get('name') or '')[:120] or None)
                 if kind in ('IVR','TimeGroup','Department','Queue') else None}
        if kind=='Agent':
            event.update(agent=str(entry.get('name') or '')[:120] or None,agent_number=agent_number(entry),
                         disposition=str(entry.get('dialst') or '')[:50] or None,
                         provider_agent_id=str(entry['id'])[:120] if entry.get('id') is not None else None)
        events.append(event)
    start = min(starts) if starts else None
    end = max(ends) if ends else None
    flow_start=start
    provider_start=None
    try:
        parsed=datetime.fromisoformat(f'{record["date"]}T{record["time"]}')
        provider_start=(parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo(source_timezone))).astimezone(UTC).isoformat()
        if not start or abs((datetime.fromisoformat(start)-datetime.fromisoformat(provider_start)).total_seconds())<=120:
            start=provider_start
            if not flow_start:warnings.append('Start timezone uses configured provider timezone; no epoch start supplied')
        else:warnings.append('Provider date/time and epoch differ; epoch retained pending timezone verification')
    except (KeyError,TypeError,ValueError):pass
    if not end and record.get('end_stamp'):
        try:
            end = datetime.fromisoformat(record['end_stamp']).replace(tzinfo=ZoneInfo(source_timezone)).astimezone(UTC).isoformat()
            warnings.append('End timezone uses configured provider timezone')
        except (ValueError,TypeError):
            pass
    status = {'answered':'ANSWERED','missed':'MISSED'}.get(str(record.get('status','')).lower(),'UNKNOWN')
    answer = min(answers) if answers else None
    if record.get('department_name') and record['department_name'] not in departments:departments.append(str(record['department_name'])[:120])
    department=departments[0] if departments else None
    participants=flow_participants(root,flow,record.get('missed_agents') or [])
    agent_answers=[e for e in events if e.get('disposition')=='Answered']
    # Resolve unnamed answer events only through a supplied agent identity.
    for event in agent_answers:
        if not event.get('agent'):
            matching=[p for p in participants if
                      (event.get('provider_agent_id') and event['provider_agent_id']==p['provider_agent_id']) or
                      (event.get('agent_number') and event['agent_number']==p['agent_number'])]
            names={p['agent_name'] for p in matching if p['agent_name']}
            if len(names)==1:event['agent']=names.pop()
    latest=max((e['at'] for e in agent_answers),default=None)
    final_events=[e for e in agent_answers if e['at']==latest]
    final_names={e['agent'] for e in final_events if e.get('agent')}
    unambiguous=bool(final_events) and len(final_names)==1 and all(e.get('agent') for e in final_events)
    final_agent=next(iter(final_names)) if unambiguous else record.get('agent_name')
    answer_source='last_answer_event' if unambiguous else 'provider_cdr' if final_agent else None
    supplied_duration=record.get('call_duration')
    duration=supplied_duration if isinstance(supplied_duration,(int,float)) and not isinstance(supplied_duration,bool) and supplied_duration>=0 else seconds(start,end)
    recording_supplied=bool(record.get('recording_url')) or record.get('recording_url_supplied') is True
    return {'projection_version':3,'id':root,'provider_call_id':provider_id,'provider_started_at':provider_start,
            'flow_started_at':flow_start,'caller':caller,'did':did,'direction':record['direction'],
            'status':status,'started_at':start,'answered_at':answer,'ended_at':end,
            'answering_agent':final_agent if status=='ANSWERED' else None,
            'answering_agent_source':answer_source if status=='ANSWERED' else None,
            'primary_department':department,'provider_department':department,'provider_departments':departments,
            'departments':departments,'legs':[], 'transfers':[],
            'participants':participants,'reported_missed_agents':[p for p in participants if p['reported_missed']],
            'provider_dtmf_input':str(record.get('dtmf_input') or '')[:100] or None,
            'provider_hangup_reason':str(record.get('reason') or '')[:120] or None,
            'provider_hangup_cause':str(record.get('hangup_cause') or '')[:120] or None,
            'attempts_available':False,'ring_attempts':None,'missed_attempts':None,
            'first_response_seconds':seconds(start,answer),'duration_seconds':duration,
            'timestamp_duration_seconds':seconds(start,end),'duration_source':'provider call_duration' if duration==supplied_duration else 'timestamp evidence',
            'warnings':warnings,'synthetic':False,'events':sorted(events,key=lambda e:(e['at'],e['event_id'])),
            'provider_answered_seconds':record.get('answered_seconds'),
            'recording_status':'provided; playback pending access/retention verification' if recording_supplied else 'unavailable from provider'}


def store_record(db, record, source_timezone='Asia/Kolkata'):
    projection = project_record(record,source_timezone)
    # Signed recording URLs may contain bearer-like tokens; they are never retained or exposed.
    raw = restricted_payload({k:v for k,v in record.items() if k != 'recording_url'})
    raw['recording_url_supplied'] = bool(record.get('recording_url')) or record.get('recording_url_supplied') is True
    content_hash = hashlib.sha256(canonical(raw).encode()).hexdigest()
    event_id = hashlib.sha256((projection['id']+content_hash).encode()).hexdigest()
    existing_event=db.get(CallEvent,event_id)
    call = db.get(Call,projection['id'])
    if existing_event and call and call.projection.get('projection_version')==3:return False
    if call:
        if (call.direction!=projection['direction'] or
            (call.caller_e164 and projection['caller'] and call.caller_e164!=projection['caller']) or
            (call.dialed_did and projection['did'] and call.dialed_did!=projection['did'])):
            raise ValueError('Conflicting provider root identity')
        projection['caller']=projection['caller'] or call.caller_e164
        projection['did']=projection['did'] or call.dialed_did
        call.caller_e164,call.dialed_did=projection['caller'],projection['did']
        old_events = {e['event_id']:e for e in call.projection.get('events',[])}
        old_events.update({e['event_id']:e for e in projection['events']})
        projection['events'] = sorted(old_events.values(), key=lambda e:(e['at'],e['event_id']))
        if 'crm' in call.projection: projection['crm'] = call.projection['crm']
    else:
        call = Call(id=projection['id'],provider='acefone',provider_call_id=projection['provider_call_id'],
                    caller_e164=projection['caller'],dialed_did=projection['did'],direction=projection['direction'])
        db.add(call)
    call.projection,call.final_status = projection,projection['status']
    call.started_at = datetime.fromisoformat(projection['started_at']) if projection['started_at'] else None
    db.flush()
    db.execute(delete(CallParticipant).where(CallParticipant.call_id==call.id))
    for participant in projection['participants']:
        db.add(CallParticipant(id=participant['id'],call_id=call.id,agent_name=participant['agent_name'],evidence=participant))
    if not existing_event:
        db.add(CallEvent(id=event_id,provider='acefone',provider_event_id=event_id,call_id=call.id,
                        event_type='CDR_SNAPSHOT',event_at=now(),dedupe_hash=content_hash,payload=raw))
        db.add(IntegrationEvent(provider='acefone',status='PROCESSED',payload=raw))
    return True
