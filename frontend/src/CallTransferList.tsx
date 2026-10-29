import type { Call } from './types';
import { localTime } from './lib';
import { missedAgents,orderedAgentEvents } from './callAgents';

export function AgentSummary({call}:{call:Call}){
  const missed=missedAgents(call);
  return <div className="agent-summary"><div><small>Agents missed · provider reported</small><strong>{missed===undefined?'Unavailable':`${missed.length} reported`}</strong><span>{missed?.map(p=>p.agent_name||'Name unavailable').join(', ')||'No missed-agent names supplied'}</span></div><div><small>Answered by</small><strong>{call.answering_agent||'No answerer supplied'}</strong><span>{call.answering_agent_source==='last_answer_event'?'Latest timestamped answer event':call.answering_agent?'Provider CDR answerer':'No confirmed answerer'}</span></div></div>;
}
export function CallTransferList({call}:{call:Call}){
  const events=orderedAgentEvents(call);const missed=missedAgents(call);
  return <div className="flow-detail"><h3>Call transfer list</h3><AgentSummary call={call}/><div className="table-wrap"><table><thead><tr><th>Time · IST</th><th>Agent</th><th>Recorded action</th></tr></thead><tbody>{events.map(e=><tr key={e.event_id}><td>{localTime(e.at)}</td><td><strong>{e.agent||call.participants?.find(p=>(e.provider_agent_id&&e.provider_agent_id===p.provider_agent_id)||(e.agent_number&&e.agent_number===p.agent_number))?.agent_name||'Name unavailable'}</strong></td><td><span className={`badge ${e.disposition==='Answered'?'answered':''}`}>{e.disposition||'Agent event'}</span></td></tr>)}</tbody></table></div>{!events.length&&<p className="muted">No timestamped agent activity supplied.</p>}<h4>Reported missed agents · time/order unavailable</h4>{missed?.length?<ul>{missed.map(p=><li key={p.id}>{p.agent_name||'Name unavailable'}</li>)}</ul>:<p className="muted">No missed-agent names supplied. This does not establish that nobody rang.</p>}</div>;
}
