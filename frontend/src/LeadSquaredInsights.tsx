import { PageSize,usePageSize,pageSizeQuery } from './PageSize';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { api,label,localTime } from './lib';
import { AgentRanking } from './AgentRanking';
import type { Agent } from './types';

type Candidate={id:string;display_name:string;created_at:string|null;current_stage:string;current_owner_name?:string|null;relationship:string};
type Row={key:string;caller:string|null;call_count:number;call_ids:string[];departments:string[];statuses:string[];first_call_at:string|null;last_call_at:string|null;match_status:string;candidates:Candidate[]};
type Report={selection_counts:{all_calls:number;department_calls:number};ranking_items:Agent[];summary:Record<string,number>;items:Row[];total:number;next_page:number|null};
export function LeadSquaredInsights({onOpen}:{onOpen:(id:string)=>void}){
  const size=usePageSize();
  const [params,setParams]=useSearchParams();const page=Number(params.get('page')||1);
  const filter=new URLSearchParams(params);filter.delete('page');filter.delete('page_size');filter.delete('show_all');filter.delete('flow_view');
  if(!filter.get('outcome'))filter.set('outcome','ANSWERED');
  else if(filter.get('outcome')==='ALL')filter.delete('outcome');
  const selected=params.get('department_selected')==='true';filter.set('department_selected',String(selected));
  const query=useQuery({queryKey:['ls-analytics',filter.toString(),page,size],queryFn:()=>api<Report>(`/reports/leadsquared?${filter}&page=${page}&${pageSizeQuery(size)}`),refetchInterval:30000});
  const summary=query.data?.summary;
  const missed=filter.get('outcome')==='MISSED';
  function missedScope(departmentOnly:boolean){const next=new URLSearchParams(params);next.set('outcome','MISSED');next.set('department_selected',String(departmentOnly));next.delete('page');setParams(next);}
  function updatePage(value:number){const next=new URLSearchParams(params);next.set('page',String(value));setParams(next);}
  function leadStatus(row:Row){return row.candidates.length?'Lead found':row.match_status==='NO_MATCH'?'Not found in last check':'Checking LeadSquared';}
  return <>
    <section className="panel crm-report-intro">
      <h2>Did our callers become leads?</h2>
      <p className="muted">Each phone number counts as one caller, even when they call more than once.</p>
      <div className="button-row">
        {!missed&&<label className="crm-scope-toggle"><input type="checkbox" checked={selected} onChange={e=>{const next=new URLSearchParams(params);next.set('department_selected',String(e.target.checked));next.delete('page');setParams(next);}}/>Only callers who reached a department</label>}
        {(filter.get('outcome')!=='ANSWERED')&&<button className="secondary" onClick={()=>{const next=new URLSearchParams(params);next.set('outcome','ANSWERED');next.delete('page');setParams(next);}}>Show answered calls</button>}
      </div>
    </section>
    {query.error&&<div className="notice error" role="alert">{query.error.message}</div>}
    {query.isPending?<p className="loading">Loading callers…</p>:summary&&<>
      {missed&&<section className="panel crm-missed-scope" aria-label="Missed call breakdown"><h2>Missed call breakdown</h2><div className="crm-missed-options"><button aria-pressed={!selected} onClick={()=>missedScope(false)}><span>All missed calls</span><strong>{query.data?.selection_counts?.all_calls??'…'}</strong></button><button aria-pressed={selected} onClick={()=>missedScope(true)}><span>Missed after department selection</span><strong>{query.data?.selection_counts?.department_calls??'…'}</strong></button></div></section>}
      <div className="kpi-grid crm-summary">{[[missed?(selected?'Missed after department selection':'Missed calls'):filter.get('outcome')==='ANSWERED'?(selected?'Answered department calls':'Answered calls'):(selected?'Department calls':'Calls'),'total_calls'],['Unique callers','unique_callers'],['Found in LeadSquared','matched_callers'],['Not found in last check','no_match_callers'],['Still being checked','unresolved_callers'],['Repeat calls','repeat_calls']].map(([title,key])=><section className="panel kpi" key={key}><div className="kpi-top">{title}</div><strong>{summary[key]}</strong></section>)}</div>
      <div className="crm-statline"><span>Already a lead before calling <strong>{summary.existing_before_call}</strong></span><span>Lead created after calling <strong>{summary.created_after_call}</strong></span></div>
      {summary.unresolved_callers>0&&<p className="muted" role="status">We’re checking {summary.unresolved_callers} callers. Their leads may already exist. Results update automatically.</p>}
      <AgentRanking agents={query.data?.ranking_items} rankingAgents={query.data?.ranking_items} rankingsOnly/>
      <section className="panel">
        <div className="panel-heading"><h2>Callers and their leads</h2></div>
        <div className="table-wrap"><table><thead><tr><th>Caller</th><th>Call date · IST</th><th>Department / call status</th><th>LeadSquared</th><th>Lead / creation date / stage</th><th>Lead owner</th></tr></thead>
          <tbody>{query.data?.items.map(row=><tr key={row.key}>
            <td><strong>{row.caller||'Number unavailable'}</strong><small>{row.call_count} {row.call_count===1?'call':'calls'}</small><details className="crm-call-links"><summary>View calls</summary>{row.call_ids.map((id,i)=><button key={id} className="text-button" onClick={()=>onOpen(id)}>Call {i+1}</button>)}</details></td>
            <td>{localTime(row.first_call_at,true)}{row.first_call_at!==row.last_call_at&&<small>Last call: {localTime(row.last_call_at,true)}</small>}</td>
            <td>{row.departments.join(', ')||'No department selected'}<small>{row.statuses.map(label).join(', ')}</small></td>
            <td><span className={`badge ${row.candidates.length?'matched':row.match_status.toLowerCase()}`}>{leadStatus(row)}</span>{row.candidates.length>1&&<small>{row.candidates.length} leads share this number</small>}</td>
            <td>{row.candidates.length?row.candidates.map(lead=><article className="crm-lead-result" key={lead.id}><strong>{lead.display_name}</strong><div>Created: {localTime(lead.created_at,true)} IST</div><div>Stage: <strong>{lead.current_stage||'Not available'}</strong></div><small>{lead.relationship==='Existing before first selected call'?'Lead existed before calling':lead.relationship==='Created after first selected call'?'Lead created after calling':'Creation date unavailable'}</small></article>):<span className="muted">{row.match_status==='NO_MATCH'?'—':'Checking…'}</span>}</td>
            <td>{row.candidates.length?row.candidates.map(lead=><article className="crm-lead-owner" key={lead.id}><strong>{lead.current_owner_name||'Owner name unavailable'}</strong>{row.candidates.length>1&&<small>{lead.display_name}</small>}</article>):<span className="muted">—</span>}</td>
          </tr>)}</tbody></table></div>
        {!query.data?.items.length&&<p className="empty">No calls match your filters. Try another date or department.</p>}
        <div className="pagination"><span>{query.data?.total} callers · page {page}</span><PageSize/><div className="button-row"><button className="text-button" disabled={page<=1} onClick={()=>updatePage(page-1)}>Previous</button><button className="text-button" disabled={!query.data?.next_page} onClick={()=>updatePage(page+1)}>Next</button></div></div>
      </section>
      <details className="crm-report-notes"><summary>How to read this report</summary><p className="muted">The filters choose the calls you want to analyse. Lead stage and owner show the latest saved LeadSquared details. “Still being checked” does not mean there is no lead. A lead created after a call does not necessarily mean the call created it. We search the standard LeadSquared leads; custom lead types are not included.</p></details>
    </>}
  </>;
}
