import { useState } from 'react';
import { useNavigate,useSearchParams } from 'react-router-dom';
import { Area,AreaChart,Bar,BarChart,CartesianGrid,Cell,Pie,PieChart,ResponsiveContainer,Tooltip,XAxis,YAxis } from 'recharts';
import { Activity,ArrowUpRight,Clock3,Phone,PhoneCall,PhoneMissed,Users } from 'lucide-react';
import type { Agent,Department,Metrics } from './types';
import { AgentRanking } from './AgentRanking';
import { duration,indiaDay } from './lib';
import { callTrend,outcomeMix } from './dashboardModel';
import './dashboard.css';

const number=(n:number)=>n.toLocaleString('en-IN');
const percent=(n:number|null|undefined)=>n==null?'—':`${(n*100).toFixed(1)}%`;
const dayLabel=(s:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',day:'numeric',month:'short'}).format(new Date(s.length===10?s+'T12:00:00+05:30':s));
const hourLabel=(s:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(s));
const tip={background:'var(--panel)',border:'1px solid var(--line)',borderRadius:12,color:'var(--text)',boxShadow:'var(--shadow)'};
export function AnalysisDashboard({metrics:m,departments,agents,rankingAgents,agentError}:{metrics?:Metrics;departments?:Department[];agents?:Agent[];rankingAgents?:Agent[];agentError?:Error|null}){
  const [params]=useSearchParams();const navigate=useNavigate();
  const [chart,setChart]=useState<'bars'|'lines'>('bars');
  const [group,setGroup]=useState<'auto'|'hour'|'day'>('auto');
  const [departmentSort,setDepartmentSort]=useState('volume');
  if(!m)return <div className="loading" role="status">Loading your dashboard…</div>;
  const days=new Set(m.hourly.map(h=>indiaDay(h.at))).size;
  const daily=group==='day'||group==='auto'&&days>2;
  const trend=callTrend(m.hourly,daily);
  const outcomes=outcomeMix(m);
  const ranked=[...(rankingAgents||[])].filter(a=>!['vadant','vadat','vadnt'].includes(a.agent.trim().toLowerCase()));
  const bestCount=Math.max(0,...ranked.map(a=>a.answered_call_count));
  const best=ranked.filter(a=>bestCount>0&&a.answered_call_count===bestCount);
  const peak=[...m.hourly].sort((a,b)=>b.total-a.total||a.at.localeCompare(b.at))[0];
  const ds=[...(departments||[])].filter(d=>d.primary_calls>0).sort((a,b)=>departmentSort==='missed'?(b.missed_primary-a.missed_primary||b.primary_calls-a.primary_calls):departmentSort==='rate'?(b.answered_primary/b.primary_calls-a.answered_primary/a.primary_calls):b.primary_calls-a.primary_calls);
  const maxDept=Math.max(1,...ds.map(d=>d.primary_calls));
  function drill(outcome?:string,department?:string,selected=false){
    const next=new URLSearchParams(params);['page','missed_department','department_selected','direction'].forEach(k=>next.delete(k));
    next.set('direction','inbound');outcome?next.set('outcome',outcome):next.delete('outcome');
    if(department)next.set('department',department);
    if(selected)next.set('missed_department','true');
    navigate('/flows?'+next.toString());
  }
  const cards=[
    {title:'Inbound calls',value:number(m.total),note:'All incoming calls',icon:Phone,action:()=>drill(),tone:'neutral'},
    {title:'Answered calls',value:number(m.ANSWERED),note:'Connected to an agent',icon:PhoneCall,action:()=>drill('ANSWERED'),tone:'answer'},
    {title:'Total missed calls',value:number(m.MISSED),note:'All unanswered incoming calls',icon:PhoneMissed,action:()=>drill('MISSED'),tone:'missed'},
    {title:'Customer missed',value:number(m.customer_missed),note:'Missed after reaching a department',icon:ArrowUpRight,action:()=>drill('MISSED',undefined,true),tone:'missed'},
    {title:'Unique callers',value:number(m.unique_callers),note:'Different caller phone numbers',icon:Users,action:()=>drill(),tone:'neutral'},
    {title:'Answer rate',value:percent(m.answer_rate),note:`${number(m.ANSWERED)} of ${number(m.total)} incoming calls`,icon:Activity,action:()=>drill('ANSWERED'),tone:'answer'},
  ];
  return <div className="analysis-dashboard">
    <div className="dash-section-line"><span className="eyebrow">PERFORMANCE SNAPSHOT</span><span>Selected dates & filters · India time</span></div>
    <div className="dash-kpis">{cards.map(c=><button className={`panel dash-kpi ${c.tone}`} key={c.title} onClick={c.action} title={`View ${c.title.toLowerCase()}`}><span className="dash-kpi-label">{c.title}<c.icon size={18}/></span><strong>{c.value}</strong><span className="dash-kpi-note">{c.note}</span><ArrowUpRight className="dash-card-link" size={15}/></button>)}</div>
    <div className="dash-charts">
      <section className="panel dash-trend" aria-labelledby="call-trend-heading">
        <div className="dash-panel-head"><div><span className="eyebrow">CALL TRAFFIC</span><h2 id="call-trend-heading">When are customers calling?</h2></div><div className="dash-chart-controls"><select aria-label="Trend grouping" value={group} onChange={e=>setGroup(e.target.value as typeof group)}><option value="auto">Auto</option><option value="hour">Hourly</option><option value="day">Daily</option></select><div className="dash-toggle" aria-label="Chart style"><button aria-pressed={chart==='bars'} onClick={()=>setChart('bars')}>Bars</button><button aria-pressed={chart==='lines'} onClick={()=>setChart('lines')}>Lines</button></div></div></div>
        <div className="dash-legend"><span><i style={{background:'var(--dash-answer)'}}/>Answered</span><span><i style={{background:'var(--dash-missed)'}}/>Total missed</span>{outcomes[3].value>0&&<span><i style={{background:'var(--dash-other)'}}/>Other / in progress</span>}<span className="dash-unit">{daily?'By day':'By hour'} · IST</span></div>
        {m.total===0?<div className="dash-empty">No calls in this selection. Try another date range.</div>:<div className="dash-chart"><ResponsiveContainer width="100%" height="100%">{chart==='bars'?<BarChart data={trend} barCategoryGap="24%" accessibilityLayer><CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 5"/><XAxis dataKey="at" tickFormatter={daily?dayLabel:hourLabel} minTickGap={28} axisLine={false} tickLine={false} tick={{fill:'var(--muted)',fontSize:12}}/><YAxis allowDecimals={false} axisLine={false} tickLine={false} width={35} tick={{fill:'var(--muted)',fontSize:12}}/><Tooltip contentStyle={tip} labelFormatter={v=>daily?dayLabel(String(v)):`${dayLabel(String(v))}, ${hourLabel(String(v))} IST`} cursor={{fill:'var(--soft)'}}/><Bar isAnimationActive={false} name="Answered" dataKey="answered" stackId="calls" fill="var(--dash-answer)" maxBarSize={38}/><Bar isAnimationActive={false} name="Total missed" dataKey="missed" stackId="calls" fill="var(--dash-missed)" maxBarSize={38}/><Bar isAnimationActive={false} name="Other / in progress" dataKey="other" stackId="calls" fill="var(--dash-other)" radius={[4,4,0,0]} maxBarSize={38}/></BarChart>:<AreaChart data={trend} accessibilityLayer><defs><linearGradient id="dash-answer-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--dash-answer)" stopOpacity={.22}/><stop offset="100%" stopColor="var(--dash-answer)" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 5"/><XAxis dataKey="at" tickFormatter={daily?dayLabel:hourLabel} minTickGap={28} axisLine={false} tickLine={false} tick={{fill:'var(--muted)',fontSize:12}}/><YAxis allowDecimals={false} axisLine={false} tickLine={false} width={35} tick={{fill:'var(--muted)',fontSize:12}}/><Tooltip contentStyle={tip} labelFormatter={v=>daily?dayLabel(String(v)):`${dayLabel(String(v))}, ${hourLabel(String(v))} IST`}/><Area isAnimationActive={false} name="Answered" type="linear" dataKey="answered" stroke="var(--dash-answer)" strokeWidth={2.5} fill="url(#dash-answer-fill)"/><Area isAnimationActive={false} name="Total missed" type="linear" dataKey="missed" stroke="var(--dash-missed)" strokeWidth={2.5} fill="transparent"/>{outcomes[3].value>0&&<Area isAnimationActive={false} name="Other / in progress" type="linear" dataKey="other" stroke="var(--dash-other)" strokeWidth={2} fill="transparent"/>}</AreaChart>}</ResponsiveContainer></div>}
        <div className="dash-chart-footer"><span><Clock3 size={15}/>Average call duration <strong>{duration(m.average_duration_seconds)}</strong></span><span><strong>{number(m.total)}</strong> incoming calls</span></div>
      </section>
      <section className="panel dash-outcomes" aria-labelledby="call-outcomes-heading"><div className="dash-panel-head"><div><span className="eyebrow">ANSWER COVERAGE</span><h2 id="call-outcomes-heading">How did calls end?</h2></div></div><div className="dash-donut"><ResponsiveContainer width="100%" height="100%"><PieChart accessibilityLayer><Pie isAnimationActive={false} data={m.total?outcomes:[{name:'No calls',value:1,color:'var(--line)'}]} dataKey="value" nameKey="name" innerRadius="72%" outerRadius="92%" startAngle={90} endAngle={-270} stroke="var(--panel)" strokeWidth={3}>{(m.total?outcomes:[{color:'var(--line)'}]).map((o,i)=><Cell key={i} fill={o.color}/>)}</Pie>{m.total>0&&<Tooltip contentStyle={tip}/>}</PieChart></ResponsiveContainer><div className="dash-donut-center"><strong>{percent(m.answer_rate)}</strong><span>answer rate</span></div></div><div className="dash-outcome-list">{outcomes.map(o=><div key={o.name}><span><i style={{background:o.color}}/>{o.name}</span><strong>{number(o.value)}<small>{m.total?(o.value/m.total*100).toFixed(1):'0.0'}%</small></strong></div>)}</div></section>
    </div>
    <div className="dash-highlights" aria-label="Business highlights">
      <article><span className="eyebrow">BUSIEST HOUR</span><strong>{peak?`${hourLabel(peak.at)}–${hourLabel(new Date(Date.parse(peak.at)+3600000).toISOString())}`:'—'}</strong><p>{peak?`${number(peak.total)} calls · ${dayLabel(peak.at)}`:'No call activity yet'}</p></article>
      <article><span className="eyebrow">MOST ANSWERED CALLS</span><strong>{best.length?best.map(a=>a.agent).join(', '):'—'}</strong><p>{best.length?`${number(bestCount)} answered${best.length>1?' each · joint highest':''}`:'No eligible answered calls'} · Support & Vadant excluded</p></article>
      <article className="dash-attention"><span className="eyebrow">CUSTOMER MISSED</span><strong>{number(m.customer_missed)} <span>calls</span></strong><p>Reached a department but were not answered</p><button onClick={()=>drill('MISSED',undefined,true)}>Review calls <ArrowUpRight size={14}/></button></article>
    </div>
    <section className="panel dash-departments" aria-labelledby="department-performance-heading"><div className="dash-panel-head"><div><span className="eyebrow">DEPARTMENT PERFORMANCE</span><h2 id="department-performance-heading">Where are calls being answered?</h2></div><select aria-label="Sort departments" value={departmentSort} onChange={e=>setDepartmentSort(e.target.value)}><option value="volume">Most calls first</option><option value="missed">Most missed first</option><option value="rate">Highest answer rate</option></select></div><div className="dash-dept-table"><div className="dash-dept-header"><span>Department</span><span>Call volume</span><span>Answered</span><span>Missed</span><span>Answer rate</span></div>{!departments?<p className="dash-empty">Loading department performance…</p>:!ds.length?<p className="dash-empty">No department calls in this selection.</p>:ds.map(d=><div className="dash-dept-row" key={d.department}><button onClick={()=>drill(undefined,d.department)}>{d.department}<ArrowUpRight size={14}/></button><div className="dash-dept-volume"><div className="dash-dept-track"><div style={{width:`${d.primary_calls/maxDept*100}%`}}><span style={{width:`${d.answered_primary/d.primary_calls*100}%`,background:'var(--dash-answer)'}}/><span style={{width:`${d.missed_primary/d.primary_calls*100}%`,background:'var(--dash-missed)'}}/><span style={{flex:1,background:'var(--dash-other)'}}/></div></div><strong>{number(d.primary_calls)}</strong></div><button className="dash-answer-count" onClick={()=>drill('ANSWERED',d.department)}>{number(d.answered_primary)}</button><button className="dash-missed-count" onClick={()=>drill('MISSED',d.department)}>{number(d.missed_primary)}</button><strong>{percent(d.answered_primary/d.primary_calls)}</strong></div>)}</div><div className="dash-chart-footer"><span>Calls are grouped by their first recorded department.</span><span>Click a count to view calls <ArrowUpRight size={14}/></span></div></section>
    <AgentRanking agents={agents} rankingAgents={rankingAgents} error={agentError}/>
  </div>;
}
