import type { Metrics } from './types';
export const weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
export const hourRange=(hour:number)=>`${String(hour).padStart(2,'0')}:00–${String((hour+1)%24).padStart(2,'0')}:00`;
const parts=new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Kolkata',weekday:'long',hour:'2-digit',hourCycle:'h23'});
export function callPatterns(rows:Metrics['hourly']){
  const grid=weekdays.map(()=>Array<number>(24).fill(0));
  for(const row of rows){
    const date=new Date(row.at);if(!Number.isFinite(date.getTime()))continue;
    const local=parts.formatToParts(date);
    const day=weekdays.indexOf(local.find(p=>p.type==='weekday')!.value);
    const hour=Number(local.find(p=>p.type==='hour')!.value);
    if(day>=0&&hour>=0&&hour<24)grid[day][hour]+=row.total;
  }
  const days=grid.map((hours,day)=>({day,name:weekdays[day],total:hours.reduce((a,b)=>a+b,0)}));
  const hours=Array.from({length:24},(_,hour)=>({hour,name:String(hour).padStart(2,'0')+':00',total:grid.reduce((n,d)=>n+d[hour],0)}));
  const dayMax=Math.max(0,...days.map(d=>d.total));const hourMax=Math.max(0,...hours.map(h=>h.total));
  const slotMax=Math.max(0,...grid.flat());
  return {grid,days,hours,total:days.reduce((n,d)=>n+d.total,0),dayMax,hourMax,slotMax,
    bestDays:days.filter(d=>dayMax>0&&d.total===dayMax),bestHours:hours.filter(h=>hourMax>0&&h.total===hourMax),
    bestSlots:grid.flatMap((row,day)=>row.flatMap((total,hour)=>slotMax>0&&total===slotMax?[{day,hour,total}]:[]))};
}
