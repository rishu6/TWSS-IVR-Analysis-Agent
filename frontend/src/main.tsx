import { Brand } from './Brand';
import { PageSize,usePageSize,pageSizeQuery } from './PageSize';
import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, NavLink, useLocation, useSearchParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query';
import { Activity, ArrowDownLeft, ArrowRight, ArrowUpRight, Building2, ChevronLeft, ChevronRight, Download, Headphones, LayoutDashboard, LogOut, Search, Settings, ShieldCheck, Users, Workflow, X } from 'lucide-react';
import type { Agent, Call, Department, Metrics, Page, Role } from './types';
import { api, dateBoundary, duration, label, localTime } from './lib';
import './style.css';
import './themes.css';
import { ThemePicker } from './ThemePicker';
import { applyTheme, savedTheme } from './themes';
import { CallTransferList } from './CallTransferList';
applyTheme(savedTheme());
import { InternalLogin, ChangePassword } from './InternalLogin';
import { InternalAdmin } from './InternalAdmin';
import { DetailedCallFlow } from './DetailedCallFlow';
import { ReportFilters } from './ReportFilters';
import { LeadSquaredInsights } from './LeadSquaredInsights';
import { AnalysisDashboard } from './AnalysisDashboard';
import { CallPatterns } from './CallPatterns';
import { CallTimeline } from './CallTimeline';

const cache = new QueryClient({defaultOptions:{queries:{retry:1, refetchOnWindowFocus:false}}});
const routes = [
  ['/', 'Overview', LayoutDashboard], ['/patterns', 'Call patterns', Activity], ['/live', 'Live calls', Activity],
  ['/flows', 'Detailed call flow', Workflow], ['/agents', 'Agent analytics', Users], ['/departments', 'Departments', Building2],
  ['/crm', 'LeadSquared insights', Workflow],
  ['/exports', 'Exports', Download], ['/admin', 'Admin', Settings],
] as const;

function Badge({value}:{value:string}) { return <span className={`badge ${value.toLowerCase().replaceAll(' ','_')}`}>{value === 'ANSWERED' && <span className="dot"/>}{label(value)}</span>; }
function ErrorBox({error}:{error:unknown}) { return <div className="notice error" role="alert">{error instanceof Error ? error.message : 'Unable to load data'}</div>; }
function Empty({text='No calls match these filters.'}:{text?:string}) { return <div className="empty"><Search size={25}/><h3>{text}</h3><p>Try a different search or clear your filters.</p></div>; }

function Login({onLogin}:{onLogin:()=>void}) {
  const [role,setRole] = useState<Role>('Manager');
  const [password,setPassword] = useState('synthetic-demo-only');
  const mutation = useMutation({mutationFn:()=>api('/auth/login',{method:'POST',body:JSON.stringify({role,password})}),onSuccess:onLogin});
  return <main className="login-page"><div className="login-story"><Brand/><span className="eyebrow">EVERY CALL HAS A STORY</span><h1>See the whole<br/>conversation.</h1><p>One customer journey. Every handoff.<br/>A clearer view of your team's day.</p><div className="story-journey"><span>Customer</span><ArrowRight/><span>Sales</span><ArrowRight/><span>Support</span></div><small>Acefone India × LeadSquared · Integration prototype</small></div><form className="login-card" onSubmit={e=>{e.preventDefault();mutation.mutate();}}><span className="pill">SYNTHETIC DATA ONLY</span><h2>Explore the workspace</h2><p>Use a demo role to review fictional calls and CRM matches.</p><label>Demo role<select value={role} onChange={e=>setRole(e.target.value as Role)}><option>Manager</option><option>Viewer</option><option>Admin</option></select></label><label>Demo password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/></label><small>Local demo default: <code>synthetic-demo-only</code></small>{mutation.error && <ErrorBox error={mutation.error}/>}<button className="primary" disabled={mutation.isPending}>Enter demo workspace <ArrowRight size={17}/></button><p className="fine"><ShieldCheck size={15}/> No provider connection. No real customer data. Role selection is a demo feature; production identity is not configured.</p></form></main>;
}

function CallTable({data,onOpen}:{data:Call[];onOpen:(id:string)=>void}) {
  if (!data.length) return <Empty/>;
  return <div className="table-wrap"><table><thead><tr><th>Caller / call ID</th><th>Time · IST</th><th>Department</th><th>Outcome</th><th>Answering agent</th><th>CRM match</th><th><span className="sr-only">Details</span></th></tr></thead><tbody>{data.map(call=><tr key={call.id}><td><div className="caller"><span className="call-icon">{call.direction==='inbound'?<ArrowDownLeft size={17}/>:<ArrowUpRight size={17}/>}</span><div><strong>{call.caller||'Caller unavailable'}</strong><small>{call.id}</small></div></div></td><td>{localTime(call.started_at,true)}<small>{call.direction}</small></td><td>{call.primary_department || 'Unassigned'}{call.departments.length>1 && <small>+{call.departments.length-1} department</small>}</td><td><Badge value={call.status}/></td><td>{call.answering_agent || '—'}</td><td><Badge value={call.crm.status}/></td><td><button className="icon-button" onClick={()=>onOpen(call.id)} aria-label={`View ${call.id}`}><ArrowUpRight size={18}/></button></td></tr>)}</tbody></table></div>;
}

function CallDrawer({id,onClose}:{id:string;onClose:()=>void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [tab,setTab] = useState<'journey'|'transfers'|'crm'>('journey');
  const query = useQuery({queryKey:['call',id],queryFn:()=>api<Call>(`/calls/${encodeURIComponent(id)}/journey`),refetchInterval:30000});
  useEffect(()=>{dialog.current?.showModal(); const prior = document.activeElement as HTMLElement; return ()=>prior?.focus();},[]);
  const call=query.data;
  return <dialog ref={dialog} className="call-drawer" onCancel={onClose} aria-labelledby="drawer-title"><div className="drawer-top"><span className="eyebrow">LOGICAL CALL JOURNEY</span><button className="icon-button" onClick={onClose} aria-label="Close call details" autoFocus><X/></button></div><h2 id="drawer-title">{call?.caller || (call?'Caller unavailable':'Loading call…')}</h2>{query.error && <ErrorBox error={query.error}/>} {call && <><div className="drawer-summary"><Badge value={call.status}/><span>{localTime(call.started_at,true)} IST</span><span>{duration(call.duration_seconds)}</span></div><div className="drawer-facts"><div><small>Final answer</small><strong>{call.answering_agent || 'No answer evidence'}</strong></div><div><small>Primary department</small><strong>{call.primary_department || 'Unavailable'}</strong></div></div><div className="tabs"><button className={tab==='journey'?'active':''} onClick={()=>setTab('journey')}>Call timeline <span>{call.events?.length}</span></button><button className={tab==='transfers'?'active':''} onClick={()=>setTab('transfers')}>Call transfer list</button><button className={tab==='crm'?'active':''} onClick={()=>setTab('crm')}>LeadSquared <span>{call.crm.candidates.length}</span></button></div>{tab==='journey'?<CallTimeline call={call}/>:tab==='transfers'?<CallTransferList call={call}/>:<div className="crm-details"><Badge value={call.crm.status}/>{!call.crm.candidates.length&&<p className="muted">{call.crm.status==='NO_MATCH'?'No lead found in the last check.':'Checking LeadSquared…'}</p>}{call.crm.candidates.length>1&&<p className="muted">{call.crm.candidates.length} leads share this number.</p>}{call.crm.candidates.map(lead=><article className="lead-card" key={lead.id}><h3>{lead.display_name}</h3><dl><dt>Current stage</dt><dd>{lead.current_stage}</dd><dt>Current owner</dt><dd>{lead.current_owner_name||'Owner name unavailable'}</dd><dt>Created</dt><dd>{localTime(lead.created_at,true)} IST</dd><dt>Source</dt><dd>{lead.source}</dd></dl></article>)}</div>}</>}</dialog>;
}

function AgentRatio({ratio,count,total}:{ratio:number|null;count:number;total:number}) {
  return <><strong>{ratio==null?'—':`${(ratio*100).toFixed(1)}%`}</strong><small>{count} / {total} total calls</small></>;
}
function AgentView({data}:{data:Agent[]}) {
  return <section className="panel"><div className="panel-heading"><div><h2>Agent performance</h2><p className="muted">Counts are distinct calls per agent. Missed counts use provider-reported evidence, not unanswered dials. An agent may miss and answer the same call.</p><p className="muted">Each ratio uses this agent’s total distinct calls in the selected filters, including calls with recorded dials. A call can be both missed and answered by the same agent, so the ratios may overlap.</p></div></div><div className="table-wrap"><table><thead><tr><th>Agent</th><th>Missed call count</th><th>Answered call count</th><th>Missed call ratio</th><th>Answered call ratio</th></tr></thead><tbody>{data.map(a=><tr key={a.agent}><td><strong>{a.agent}</strong></td><td><span className="badge missed">{a.missed_call_count??0}</span></td><td><span className="badge answered">{a.answered_call_count??0}</span></td><td><AgentRatio ratio={a.missed_call_ratio} count={a.missed_call_count} total={a.total_call_count}/></td><td><AgentRatio ratio={a.answered_call_ratio} count={a.answered_call_count} total={a.total_call_count}/></td></tr>)}</tbody></table>{data.length===0&&<Empty text="No agent outcomes match these filters."/>}</div></section>;
}

function DepartmentView({data}:{data:Department[]}) { return <><div className="notice">Calls are attributed to their first evidenced department. Transfer involvement includes both departments; involvement counts are not additive.</div><div className="department-grid">{data.map(d=><section className="panel department-card" key={d.department}><span className="department-icon"><Building2/></span><h2>{d.department}</h2><strong className="large-number">{d.primary_calls}</strong><span className="muted">primary inbound calls</span><div className="department-stat"><span>Answered primary calls</span><strong>{d.answered_primary}</strong></div><div className="department-stat"><span>Calls involving department</span><strong>{d.involved_calls}</strong></div></section>)}</div></>; }

function Workspace({role,onLogout,demo,name}:{role:Role;onLogout:()=>void;demo:boolean;name:string}) {
  const location=useLocation(); const [params,setParams]=useSearchParams();
  const tabFilters=useRef<Record<string,string>>({});
  useEffect(()=>{tabFilters.current[location.pathname]=location.search;},[location.pathname,location.search]);
  const tabLink=(href:string)=>href+(href===location.pathname?location.search:tabFilters.current[href]||'');
  const [selected,setSelected]=useState<string|null>(null);
  const [socketStatus,setSocketStatus]=useState('Polling every 30s');
  const [exportError,setExportError]=useState<unknown>(null);
  const [exporting,setExporting]=useState(false);
  const [passwordDialog,setPasswordDialog]=useState(false);
  const path=location.pathname;
  const options=useQuery({queryKey:['filter-options'],queryFn:()=>api<{departments:string[];agents:string[];stages:string[];owners:string[]}>('/filter-options')});
  const current=routes.find(r=>r[0]===path);
  const filterParams = new URLSearchParams(params);
  filterParams.delete('page');if(path!=='/flows')filterParams.delete('missed_department');
  if (path==='/live') filterParams.set('outcome','IN_PROGRESS');
  if(path==='/crm'&&!filterParams.get('outcome'))filterParams.set('outcome','ANSWERED');
  if(filterParams.get('outcome')==='ALL')filterParams.delete('outcome');
  const filter=filterParams.toString();
  const size=usePageSize();
  const page=Number(params.get('page')||1);
  const calls=useQuery({queryKey:['calls',filter,page,size],queryFn:()=>api<Page>(`/calls?${filter}&page=${page}&${pageSizeQuery(size)}`),refetchInterval:30000});
  const metrics=useQuery({queryKey:['metrics',filter],queryFn:()=>api<Metrics>(`/metrics/overview?${filter}`),refetchInterval:30000});
  const agentFilter=new URLSearchParams(filter);if(path==='/'){agentFilter.set('direction','inbound');agentFilter.set('ranking_exclude_department','Support');}
  const agents=useQuery({queryKey:['agents',agentFilter.toString()],queryFn:()=>api<{items:Agent[];ranking_items?:Agent[]}>(`/reports/agents?${agentFilter}`),enabled:path==='/agents'||path==='/',refetchInterval:30000});
  const departments=useQuery({queryKey:['departments',filter],queryFn:()=>api<{items:Department[]}>(`/reports/departments?${filter}`),enabled:path==='/departments'||path==='/',refetchInterval:30000});
  const health=useQuery({queryKey:['health'],queryFn:()=>api<{mode:string;acefone:string;leadsquared:string;live_verified:boolean}>('/integrations/health')});
  const status=useQuery({queryKey:['status'],queryFn:()=>api<{last_successful_sync:string;dataset_at:string;mode:string;providers?:Record<string,{status:string}>}>('/integrations/status'),refetchInterval:30000});
  const callSyncLabel=status.data?.providers?.acefone?.status==='ERROR'?'Call sync failed · retrying':status.data?.providers?.acefone?.status==='SYNCING'?'Importing calls…':!status.data?.last_successful_sync?'Waiting for first call sync':Date.now()-Date.parse(status.data.last_successful_sync)>300000?'Call sync delayed · check Admin':'Call sync active';
  const retryCRM=useMutation({mutationFn:()=>api('/demo/retry-crm',{method:'POST'}),onSuccess:()=>cache.invalidateQueries()});
  useEffect(()=>{
    let socket:WebSocket|undefined, stopped=false;
    api<{token:string}>('/live-token',{method:'POST'}).then(({token})=>{
      if(stopped)return;
      socket=new WebSocket(`${locationProtocol()}//${window.location.host}/api/v1/live`);
      socket.onopen=()=>socket?.send(token);
      socket.onmessage=()=>{setSocketStatus(demo?'Connected · synthetic updates':'Dashboard connected');cache.invalidateQueries({predicate:q=>q.queryKey[0]!=='auth'});};
      socket.onerror=()=>setSocketStatus('Polling every 30s');
      socket.onclose=()=>setSocketStatus('Polling every 30s');
    }).catch(()=>setSocketStatus('Polling every 30s'));
    return()=>{stopped=true;socket?.close();};
  },[]);
  function update(key:string,value:string) { const next=new URLSearchParams(params); next.delete('page'); value?next.set(key,value):next.delete(key);setParams(next); }
  async function download(format:'csv'|'xlsx') {
    setExporting(true);setExportError(null);
    try {
      const response=await fetch(`/api/v1/reports/exports?${filter}&format=${format}`,{credentials:'same-origin'});
      if(!response.ok)throw new Error((await response.json()).detail);
      const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=`${demo?'synthetic-calls':'calls'}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }catch(error){setExportError(error);}finally{setExporting(false);}
  }
  const description:Record<string,string>={'/flows':'Inspect answered and missed calls, all provider flow steps and previous dates.','/':'Your call performance, clearly in focus.','/patterns':'Find the busiest weekdays and hours for incoming calls.','/live':'In-progress calls require verified live-call events; CDR polling shows completed history.','/calls':'Follow every leg, handoff and outcome in one place.','/agents':'Understand answered legs and missed ring attempts.','/departments':'See routing and transfer involvement across teams.','/crm':'See which callers are in LeadSquared, their lead stage and owner.','/recovery':'Find possible recoveries without merging customer calls.','/exports':'Download a report of the currently filtered synthetic calls.','/admin':'Integration readiness and demo access controls.'};
  if(passwordDialog)return <ChangePassword onChanged={()=>setPasswordDialog(false)} onCancel={()=>setPasswordDialog(false)}/>;
  if(['/calls','/recovery'].includes(path))return <Navigate to={'/flows'+location.search} replace/>;
  return <div className="app-shell"><aside className="sidebar"><Brand/><span className="workspace-name">TWSS WORKSPACE <span>{demo?'DEMO':'INTERNAL'}</span></span><nav aria-label="Main navigation">{routes.map(([href,title,Icon])=><React.Fragment key={href}>{href==='/exports' && <div className="nav-divider"/>}<NavLink to={tabLink(href)} end={href==='/'} className={({isActive})=>isActive?'nav-link active':'nav-link'}><Icon size={18}/>{title}{href==='/live' && <span className="live-dot"/>}</NavLink></React.Fragment>)}</nav><div className="sidebar-bottom"><div className="integration-card"><span className="integration-orbit"><Headphones size={21}/></span><strong>Explore your calls</strong><p>See who answered and follow each customer’s call journey.</p><NavLink to={tabLink('/flows')}>View call details <ArrowUpRight size={15}/></NavLink></div><div className="user-card"><span className="avatar">{role.slice(0,1)}D</span><div><strong>{name}</strong><small>Local workspace</small></div><button className="icon-button" aria-label="Sign out" onClick={()=>api('/auth/logout',{method:'POST'}).finally(onLogout)}><LogOut size={17}/></button></div></div></aside><div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={13}/><strong>{current?.[1]||'Page not found'}</strong></div><div className="top-actions"><span className="top-demo">{demo?'SYNTHETIC DEMO':'INTERNAL WORKSPACE'}</span><ThemePicker/><button className="top-avatar" aria-label="Change your password" disabled={demo} onClick={()=>setPasswordDialog(true)}>{role[0]}</button></div></header><main className="content"><div className="page-title"><div><span className="eyebrow">TELEPHONY INTELLIGENCE</span><h1>{path==='/'?'Analysis dashboard':current?.[1]||'Page not found'}</h1><p>{description[path]||'Choose a page from the navigation.'}</p></div><button className="secondary" disabled={role==='Viewer'||exporting} title={role==='Viewer'?'Manager or Admin required':'Export current filters to CSV'} onClick={()=>download('csv')}><Download size={16}/>Export report</button></div><div className="demo-banner"><span><span className="amber-dot"/> {demo?'Demo data · 27 Oct 2026 · fictional callers':'Account data · Acefone India · syncs while app is awake'}</span><span>{demo?socketStatus:callSyncLabel}<span className="separator">|</span> {demo?'Last replay':'Last sync'} {localTime(status.data?.last_successful_sync)} IST</span></div><ReportFilters key={path} defaultOutcome={path==='/crm'?'ANSWERED':''} departments={options.data?.departments||[]} showDates={path!=='/flows'} live={path==='/live'}/><section className="filters" aria-label="Report filters"><div className="search-field"><Search size={17}/><input aria-label="Search calls" placeholder="Search caller, call ID, DID or agent…" value={params.get('q')||''} onChange={e=>update('q',e.target.value)}/></div><details className="more-filters"><summary>More filters <span>{filterParams.size>0?filterParams.size:''}</span></summary><div className="filter-popover"><label>Agent<select value={params.get('agent')||''} onChange={e=>update('agent',e.target.value)}><option value="">All agents</option>{(options.data?.agents||[]).map(a=><option key={a}>{a}</option>)}</select></label><label>DID<input value={params.get('did')||''} onChange={e=>update('did',e.target.value)} placeholder="Exact DID in E.164"/></label><label>Lead stage<select value={params.get('stage')||''} onChange={e=>update('stage',e.target.value)}><option value="">All stages</option>{(options.data?.stages||[]).map(s=><option key={s}>{s}</option>)}</select></label><label>Lead owner<select value={params.get('owner')||''} onChange={e=>update('owner',e.target.value)}><option value="">All owners</option>{(options.data?.owners||[]).map(owner=><option key={owner}>{owner}</option>)}</select></label><button className="text-button" onClick={()=>setParams({})}>Clear all filters</button></div></details>{params.size>0 && <button className="icon-button" aria-label="Clear filters" onClick={()=>setParams({})}><X size={16}/></button>}</section>{(calls.error||metrics.error||agents.error||departments.error) && <ErrorBox error={calls.error||metrics.error||agents.error||departments.error}/>} {!!exportError && <ErrorBox error={exportError}/>}
    {path==='/patterns' && <CallPatterns metrics={metrics.data}/>}
    {path==='/crm' && <LeadSquaredInsights onOpen={setSelected}/>}
    {path==='/flows' && <DetailedCallFlow role={role} demo={demo} onOpen={setSelected}/>}
    {path==='/' && <AnalysisDashboard metrics={metrics.data} departments={departments.data?.items} agents={agents.data?.items} rankingAgents={agents.data?.ranking_items} agentError={agents.error}/>}
    {['/live'].includes(path) && <>{path==='/crm' && <div className="notice">All candidates are preserved. Stage and ownership are current only. First observed caller and new CRM lead are separate concepts.{demo && role!=='Viewer' && <button className="text-button" disabled={retryCRM.isPending} onClick={()=>retryCRM.mutate()}>Simulate CRM recovery <ArrowRight size={15}/></button>}{retryCRM.isSuccess && <span>Simulated recovery applied.</span>}{retryCRM.error && <ErrorBox error={retryCRM.error}/>}</div>}<section className="panel"><div className="panel-heading"><div><h2>{path==='/live'?'In-progress calls':path==='/crm'?'Caller-to-lead matches':'All call journeys'}</h2><p className="muted">{calls.data?.total??'…'} logical calls · times shown in Asia/Kolkata</p></div></div>{calls.isPending?<div className="loading">Loading calls…</div>:<CallTable data={calls.data?.items||[]} onOpen={setSelected}/>}<div className="pagination"><span>Page {page} · {calls.data?.total??0} calls</span><PageSize/><div><button className="icon-button" aria-label="Previous page" disabled={page<=1} onClick={()=>setParams(p=>{const n=new URLSearchParams(p);n.set('page',String(page-1));return n;})}><ChevronLeft size={18}/></button><button className="icon-button" aria-label="Next page" disabled={!calls.data?.next_page} onClick={()=>setParams(p=>{const n=new URLSearchParams(p);n.set('page',String(page+1));return n;})}><ChevronRight size={18}/></button></div></div></section></>}
    {path==='/agents' && <AgentView data={agents.data?.items||[]}/>}
    {path==='/departments' && <DepartmentView data={departments.data?.items||[]}/>}
    {path==='/exports' && <section className="panel export-panel"><Download size={30}/><h2>Your filtered report, ready to share.</h2><p className="muted">{calls.data?.total??0} {demo?'synthetic':'account'} calls match the filters. Exports include call identifiers, callers, outcomes and primary department. Timestamps use UTC.</p><div className="button-row"><button className="primary" disabled={role==='Viewer'||exporting} onClick={()=>download('csv')}>Download CSV <Download size={16}/></button><button className="secondary" disabled={role==='Viewer'||exporting} onClick={()=>download('xlsx')}>Download XLSX <Download size={16}/></button></div><small>{role==='Viewer'?'Your Viewer role cannot export reports.':'Manager and Admin exports are recorded in the audit log.'}</small></section>}
    {path==='/admin' && !demo && (role==='Admin'?<InternalAdmin/>:<div className="notice">Admin access required. Your current role is {role}.</div>)}{path==='/admin' && demo && (role!=='Admin'?<div className="notice">Admin access required. Your current role is {role}.</div>:<section className="panel admin-panel"><h2>Integration readiness</h2><p className="muted">Read-only demo configuration. Production integration management is pending verified contracts.</p><div className="integration-row"><div><strong>Acefone India</strong><p>Live history, webhook mapping, ring coverage and recording access unverified.</p></div><Badge value={health.data?.acefone||'LOADING'}/></div><div className="integration-row"><div><strong>LeadSquared</strong><p>Phone lookup documented; complete duplicate enumeration needs tenant validation.</p></div><Badge value={health.data?.leadsquared||'LOADING'}/></div><div className="integration-row"><div><strong>Authentication</strong><p>Opaque one-hour demo sessions. Admin, Manager, Viewer. Production SSO/MFA pending.</p></div><Badge value="DEMO_ONLY"/></div><div className="notice">Live mode is disabled at startup. Provider credentials are not stored or exposed. Department mappings and agents are fixture-defined; management is not implemented.</div></section>)}
    <footer className="page-footer"><span>TWSS IVR <span>·</span> Acefone India × LeadSquared</span><span>Evidence first. Every journey preserved.</span></footer></main></div>{selected && <CallDrawer key={selected} id={selected} onClose={()=>setSelected(null)}/>}</div>;
}

function locationProtocol(){return window.location.protocol==='https:'?'wss:':'ws:';}
function App(){
  useEffect(()=>{
    const expired=()=>{cache.removeQueries({predicate:q=>!['auth','login-configuration'].includes(String(q.queryKey[0]))});cache.setQueryData(['auth'],null);};
    window.addEventListener('session-expired',expired);
    return()=>window.removeEventListener('session-expired',expired);
  },[]);
  const config=useQuery({queryKey:['login-configuration'],queryFn:()=>api<{demo:boolean}>('/auth/configuration')});
  const auth=useQuery({queryKey:['auth'],queryFn:()=>api<{role:Role;demo:boolean;display_name:string;must_change_password:boolean}>('/auth/me'),retry:false});
  if(auth.isPending||config.isPending)return <div className="loading">Opening workspace…</div>;
  const refresh=()=>cache.invalidateQueries({queryKey:['auth']});
  if(!auth.data)return config.data?.demo===false?<InternalLogin onLogin={refresh}/>:<Login onLogin={refresh}/>;
  if(auth.data.must_change_password)return <ChangePassword onChanged={refresh}/>;
  return <Workspace role={auth.data.role} demo={auth.data.demo} name={auth.data.display_name} onLogout={()=>{cache.clear();auth.refetch();}}/>;
}

createRoot(document.getElementById('root')!).render(<QueryClientProvider client={cache}><BrowserRouter><App/></BrowserRouter></QueryClientProvider>);
