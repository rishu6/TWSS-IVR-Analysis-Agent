"""Filtered call-to-lead analytics from saved, read-only CRM evidence."""
import hashlib
from datetime import UTC
from sqlalchemy import select
from .db import Lead,LeadPhone
from .domain import timestamp
from .reports import has_department_flow,mask_phone
from .owner_directory import owner_names,resolve_owner_name


def analytics(db,calls,role,department_selected=True):
    calls=[c for c in calls if not department_selected or has_department_flow(c.projection)]
    ids={lead['id'] for c in calls for lead in c.projection.get('crm',{}).get('candidates',[]) if lead.get('id')}
    # Positive matches in the saved index are usable immediately, even if the
    # per-call projection has not yet been refreshed by the background worker.
    indexed={}
    numbers=list({c.caller_e164 for c in calls if c.caller_e164 and not c.projection.get('crm',{}).get('candidates')})
    for offset in range(0,len(numbers),500):
        for phone,lead_id in db.execute(select(LeadPhone.normalized_number,LeadPhone.lead_id).where(
                LeadPhone.normalized_number.in_(numbers[offset:offset+500]))):
            indexed.setdefault(phone,set()).add(lead_id)
            ids.add(lead_id)
    current={}
    owners=owner_names(db)
    ids=list(ids)
    for offset in range(0,len(ids),500):
        for lead in db.scalars(select(Lead).where(Lead.id.in_(ids[offset:offset+500]))):
            current[lead.id]={'id':lead.id,'display_name':lead.display_name,'created_at':lead.created_at.replace(tzinfo=UTC).isoformat(),
                'current_stage':lead.current_stage,'current_owner':lead.current_owner,'synced_at':lead.last_synced_at.replace(tzinfo=UTC).isoformat()}
    groups={}
    for call in calls:
        key=call.caller_e164 or 'unknown:'+call.id
        group=groups.setdefault(key,{'key':hashlib.sha256(key.encode()).hexdigest()[:24],
            'caller':call.caller_e164,'call_count':0,'call_ids':[],'departments':set(),'statuses':set(),
            'first_call_at':None,'last_call_at':None,'candidates':{},'crm_statuses':set(),'stale':False,'synced_at':None})
        p=call.projection;crm=p.get('crm',{})
        group['call_count']+=1;group['call_ids'].append(call.id)
        group['departments'].update(p.get('departments',[]));group['statuses'].add(p['status'])
        at=p.get('started_at')
        if at:
            if not group['first_call_at'] or timestamp(at)<timestamp(group['first_call_at']):group['first_call_at']=at
            if not group['last_call_at'] or timestamp(at)>timestamp(group['last_call_at']):group['last_call_at']=at
        group['crm_statuses'].add(crm.get('status','PENDING'))
        group['stale']|=bool(crm.get('stale')) or str(crm.get('status','')).startswith('ERROR')
        if crm.get('synced_at') and (not group['synced_at'] or timestamp(crm['synced_at'])<timestamp(group['synced_at'])):
            group['synced_at']=crm['synced_at']
        for lead_id in indexed.get(call.caller_e164,[]):
            if lead_id in current:group['candidates'][lead_id]=dict(current[lead_id])
        for candidate in crm.get('candidates',[]):
            group['candidates'][candidate['id']]=dict(current.get(candidate['id'],candidate))
    summary=dict(total_calls=len(calls),unique_callers=0,repeat_calls=0,matched_callers=0,no_match_callers=0,
        unresolved_callers=0,multiple_match_callers=0,existing_before_call=0,created_after_call=0,
        creation_date_unknown=0,unknown_caller_calls=0,matched_calls=0)
    items=[]
    for group in groups.values():
        candidates=list(group['candidates'].values())
        for lead in candidates:
            lead['current_owner_name']=resolve_owner_name(lead.get('current_owner'),owners)
            lead['display_name']='Restricted lead' if role=='Viewer' else lead.get('display_name','Name unavailable')
            try:
                lead['relationship']='Existing before first selected call' if timestamp(lead['created_at'])<=timestamp(group['first_call_at']) else 'Created after first selected call'
            except (ValueError,KeyError,TypeError,AttributeError):lead['relationship']='Creation date unavailable'
        group['candidates']=candidates
        known=bool(group['caller'])
        group['match_status']='MULTIPLE_MATCHES' if len(candidates)>1 else 'MATCHED' if candidates else 'NO_MATCH' if group['crm_statuses']=={'NO_MATCH'} and not group['stale'] else 'UNRESOLVED'
        if known:
            summary['unique_callers']+=1;summary['repeat_calls']+=group['call_count']-1
            if candidates:
                summary['matched_callers']+=1;summary['matched_calls']+=group['call_count']
                summary['multiple_match_callers']+=len(candidates)>1
                relationships={lead['relationship'] for lead in candidates}
                if 'Existing before first selected call' in relationships:summary['existing_before_call']+=1
                elif 'Creation date unavailable' in relationships:summary['creation_date_unknown']+=1
                else:summary['created_after_call']+=1
            elif group['match_status']=='NO_MATCH':summary['no_match_callers']+=1
            else:summary['unresolved_callers']+=1
        else:summary['unknown_caller_calls']+=group['call_count']
        group['caller']=mask_phone(group['caller']) if role=='Viewer' else group['caller']
        group['departments']=sorted(group['departments']);group['statuses']=sorted(group['statuses']);group.pop('crm_statuses')
        items.append(group)
    items.sort(key=lambda x:x['first_call_at'] or '',reverse=True)
    return summary,items
