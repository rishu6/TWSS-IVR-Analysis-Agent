import type { Call,Participant } from './types';

export function missedAgents(call:Pick<Call,'reported_missed_agents'|'participants'>):Participant[]|undefined {
  const rows=call.reported_missed_agents??call.participants?.filter(p=>p.reported_missed);
  if(!rows)return undefined;
  const seen=new Set<string>();
  return rows.filter(p=>{const key=p.provider_agent_id||p.agent_number||p.agent_name||p.id;if(seen.has(key))return false;seen.add(key);return true;});
}
export function orderedAgentEvents(call:Pick<Call,'events'>){
  return (call.events||[]).filter(e=>e.type==='Agent').slice().sort((a,b)=>Date.parse(a.at)-Date.parse(b.at));
}
