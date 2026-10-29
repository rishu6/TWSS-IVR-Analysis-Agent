"""Per-agent logical call counts and conservative recorded-flow positions."""
from collections import Counter


def outcome_report(calls):
    groups={}
    for row in calls:
        call=row.projection
        participants=call.get('participants',[])
        def name(event):
            if event.get('agent'):return event['agent']
            matches={p['agent_name'] for p in participants if p.get('agent_name') and (
                event.get('provider_agent_id') and event['provider_agent_id']==p.get('provider_agent_id') or
                event.get('agent_number') and event['agent_number']==p.get('agent_number'))}
            return next(iter(matches)) if len(matches)==1 else None
        # Deduplicate exact events; do not impose an ordering on simultaneous dials.
        events=list({e.get('event_id',str(e)):e for e in call.get('events',[])}.values())
        if call.get('synthetic'):
            dials=sorted([e for e in events if e['type']=='RING'],key=lambda e:e['at'])
        else:
            dials=sorted([e for e in events if e['type']=='Agent' and e.get('disposition')=='Dialed'],key=lambda e:e['at'])
        times=Counter(e['at'] for e in dials)
        positions={e.get('event_id'):i+1 if times[e['at']]==1 else None for i,e in enumerate(dials)}
        answered,missed={},{}
        for event in events:
            answered_event=event['type']=='ANSWER' or event['type']=='Agent' and event.get('disposition')=='Answered'
            missed_event=bool(call.get('synthetic')) and event['type']=='NO_ANSWER'
            if not (answered_event or missed_event):continue
            agent=name(event)
            if not agent:continue
            if call.get('synthetic'):
                candidates=[e for e in dials if e.get('leg_id') and e['leg_id']==event.get('leg_id') and e['at']<=event['at']]
            else:
                # Without leg IDs, repeated dials cannot be linked to one answer safely.
                candidates=[e for e in dials if name(e)==agent and e['at']<=event['at']]
            position=positions.get(candidates[0].get('event_id')) if len(candidates)==1 else None
            (answered if answered_event else missed).setdefault(agent,set()).add(position)
        if call.get('status')=='ANSWERED' and call.get('answering_agent'):
            answered.setdefault(call['answering_agent'],{None})
        for person in call.get('reported_missed_agents',[]):
            if person.get('agent_name'):missed.setdefault(person['agent_name'],{None})
        involved=set(answered)|set(missed)|{name(e) for e in dials if name(e)}
        for agent in involved:
            group=groups.setdefault(agent,dict(agent=agent,answered_call_count=0,missed_call_count=0,
                total_call_count=0,answered_by_attempt={},missed_by_attempt={}))
            group['total_call_count']+=1
        for kind,agents in (('answered',answered),('missed',missed)):
            for agent,evidence in agents.items():
                group=groups.setdefault(agent,dict(agent=agent,answered_call_count=0,missed_call_count=0,
                    answered_by_attempt={},missed_by_attempt={}))
                group[kind+'_call_count']+=1
                # One category per agent/call; multiple answers/misses remain unassigned.
                position=next(iter(evidence)) if len(evidence)==1 else None
                key=str(position) if position else 'unknown'
                counts=group[kind+'_by_attempt'];counts[key]=counts.get(key,0)+1
    for group in groups.values():
        total=group['total_call_count']
        group['missed_call_ratio']=group['missed_call_count']/total if total else None
        group['answered_call_ratio']=group['answered_call_count']/total if total else None
    return groups
