import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis } from 'recharts';
import { CalendarDays,Clock3,Flame } from 'lucide-react';
import type { Metrics } from './types';
import { indiaDay,shiftDay } from './lib';
import { callPatterns,hourRange,weekdays } from './callPatternsModel';
import './callPatterns.css';
export function CallPatterns({metrics}:{metrics?:Metrics}){
  const [params,setParams]=useSearchParams();
  const [day,setDay]=useState('all');const [slot,setSlot]=useState<{day:number;hour:number}|null>(null);
  function week(previous:boolean){const today=indiaDay();const offset=(new Date(today+'T12:00:00Z').getUTCDay()+6)%7;
    const start=shiftDay(today,-offset-(previous?7:0));const end=previous?shiftDay(start,6):today;
    const next=new URLSearchParams(params);next.delete('page');next.set('start',new Date(start+'T00:00:00+05:30').toISOString());next.set('end',new Date(shiftDay(end,1)+'T00:00:00+05:30').toISOString());setParams(next);
  }
  if(!metrics)return <div className="loading" role="status">Loading call patterns…</div>;
  const p=callPatterns(metrics.hourly);
  const hours=day==='all'?p.hours:p.hours.map(h=>({...h,total:p.grid[Number(day)][h.hour]}));
  const tied=(n:number)=>n>1?' · tied for highest':'';
  return <div className="call-patterns">
    <div className="patterns-intro"><p>Find the busiest weekdays and hours to plan your team’s availability. Counts use incoming calls in the selected dates and filters.</p><div className="button-row"><button className="secondary" onClick={()=>week(false)}>This week</button><button className="secondary" onClick={()=>week(true)}>Last week</button></div></div>
    {!p.total?<section className="panel dash-empty">No calls with a recorded time match these filters. Try another date range.</section>:<>
      <div className="patterns-kpis">
        <article className="panel"><span className="eyebrow"><CalendarDays size={16}/>BUSIEST DAY OF THE WEEK</span><strong>{p.bestDays.map(d=>d.name).join(', ')}</strong><p>{p.dayMax.toLocaleString('en-IN')} calls{tied(p.bestDays.length)}</p></article>
        <article className="panel"><span className="eyebrow"><Clock3 size={16}/>BUSIEST TIME OF DAY · IST</span><strong>{p.bestHours.map(h=>hourRange(h.hour)).join(', ')}</strong><p>{p.hourMax.toLocaleString('en-IN')} calls{tied(p.bestHours.length)}</p></article>
        <article className="panel"><span className="eyebrow"><Flame size={16}/>PEAK WEEKLY TIME SLOT</span><strong>{p.bestSlots.length===1?`${weekdays[p.bestSlots[0].day]} · ${hourRange(p.bestSlots[0].hour)}`:`${p.bestSlots.length} equally busy slots`}</strong><p>{p.slotMax.toLocaleString('en-IN')} calls in each top slot</p></article>
      </div>
      <div className="patterns-charts">
        <section className="panel"><div className="dash-panel-head"><div><span className="eyebrow">WEEKDAY COMPARISON</span><h2>Which days receive the most calls?</h2></div></div><div className="patterns-days">{p.days.map(d=><button key={d.day} className={day===String(d.day)?'active':''} onClick={()=>{setDay(day===String(d.day)?'all':String(d.day));setSlot(null);}} aria-pressed={day===String(d.day)}><span>{d.name}</span><div className="patterns-day-track"><div style={{width:`${d.total/p.dayMax*100}%`}}/></div><strong>{d.total}</strong></button>)}</div><div className="dash-chart-footer">Select a weekday to see its hourly pattern.</div></section>
        <section className="panel"><div className="dash-panel-head"><div><span className="eyebrow">HOURLY CALL VOLUME · IST</span><h2>When should your team be available?</h2></div><select aria-label="Weekday for hourly calls" value={day} onChange={e=>{setDay(e.target.value);setSlot(null);}}><option value="all">All weekdays</option>{weekdays.map((name,i)=><option value={i} key={name}>{name}</option>)}</select></div><div className="patterns-hour-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={hours} accessibilityLayer><CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 5"/><XAxis dataKey="name" tick={{fill:'var(--muted)',fontSize:11}} minTickGap={20} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} width={30} tick={{fill:'var(--muted)',fontSize:12}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:'var(--panel)',color:'var(--text)',border:'1px solid var(--line)',borderRadius:10}} cursor={{fill:'var(--soft)'}}/><Bar isAnimationActive={false} dataKey="total" name="Incoming calls" fill="var(--green)" radius={[4,4,0,0]} maxBarSize={24}/></BarChart></ResponsiveContainer></div><div className="dash-chart-footer">{day==='all'?'All weekdays':weekdays[Number(day)]} · {hours.reduce((n,h)=>n+h.total,0)} calls</div></section>
      </div>
      <section className="panel patterns-heatmap"><div className="dash-panel-head"><div><span className="eyebrow">WEEKLY CALL HEATMAP · IST</span><h2>Your busiest day and time, together</h2></div><span className="muted">Darker colour = more calls</span></div><div className="patterns-heatmap-scroll"><table aria-label="Calls by weekday and hour"><thead><tr><th>Day / hour</th>{p.hours.map(h=><th key={h.hour}>{String(h.hour).padStart(2,'0')}</th>)}<th>Total</th></tr></thead><tbody>{p.grid.map((row,d)=><tr key={d}><th scope="row">{weekdays[d]}</th>{row.map((count,h)=><td key={h}><button className={slot?.day===d&&slot.hour===h?'active':''} aria-label={`${weekdays[d]} ${hourRange(h)} IST: ${count} calls`} title={`${weekdays[d]} ${hourRange(h)} IST: ${count} calls`} onClick={()=>{setSlot({day:d,hour:h});setDay(String(d));}} style={{background:count?`color-mix(in srgb, var(--green) ${18+count/p.slotMax*72}%, var(--panel))`:'var(--surface-alt)',color:count/p.slotMax>.55?'var(--panel)':'var(--text)'}}>{count||'·'}</button></td>)}<td><strong>{p.days[d].total}</strong></td></tr>)}</tbody></table></div><div className="dash-chart-footer" role="status">{slot?`${weekdays[slot.day]} · ${hourRange(slot.hour)} IST · ${p.grid[slot.day][slot.hour]} calls`:'Select a cell to inspect a weekday and hour.'}<span>{p.total.toLocaleString('en-IN')} incoming calls analysed</span></div></section>
      <p className="muted">Totals combine the same weekday and hour across your selected dates.{metrics.total>p.total?` ${metrics.total-p.total} calls have no recorded start time and are excluded from these charts.`:''}</p>
    </>}
  </div>;
}
