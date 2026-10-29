import type { Metrics } from './types';
import { indiaDay } from './lib';
export type TrendPoint={at:string;answered:number;missed:number;other:number;total:number};
export function callTrend(hourly:Metrics['hourly'],daily:boolean):TrendPoint[]{
  const buckets=new Map<string,TrendPoint>();
  for(const row of hourly){
    const at=daily?indiaDay(row.at):row.at;
    const group=buckets.get(at)||{at,answered:0,missed:0,other:0,total:0};
    group.answered+=row.answered;group.missed+=row.missed;
    group.other+=Math.max(0,row.total-row.answered-row.missed);group.total+=row.total;
    buckets.set(at,group);
  }
  if(!buckets.size)return [];
  const keys=[...buckets.keys()].sort();
  const start=Date.parse(daily?keys[0]+'T00:00:00+05:30':keys[0]);
  const end=Date.parse(daily?keys.at(-1)+'T00:00:00+05:30':keys.at(-1)!);
  const step=daily?86400000:3600000;
  // Cap very long historical ranges; never interpolate made-up call counts.
  if((end-start)/step>730)return [...buckets.values()].sort((a,b)=>a.at.localeCompare(b.at));
  const result=[];
  for(let t=start;t<=end;t+=step){
    const at=daily?indiaDay(new Date(t)):new Date(t).toISOString();
    const row=daily?buckets.get(at):hourly.find(r=>Date.parse(r.at)===t);
    result.push(row?{at,answered:row.answered,missed:row.missed,other:Math.max(0,row.total-row.answered-row.missed),total:row.total}:{at,answered:0,missed:0,other:0,total:0});
  }
  return result;
}
export function outcomeMix(m:Metrics){return [
  {name:'Answered',value:m.department_answered,color:'var(--dash-answer)'},
  {name:'Missed',value:m.customer_missed,color:'var(--dash-missed)'},
  {name:'Other / in progress',value:Math.max(0,m.department_calls-m.department_answered-m.customer_missed),color:'var(--dash-other)'}
];}
