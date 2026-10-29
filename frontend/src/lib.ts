export function localTime(value:string|null|undefined, date=false):string {
  if (!value) return 'Unavailable';
  const instant=new Date(/^\d{4}-\d{2}-\d{2}T/.test(value)&&!/(Z|[+-]\d{2}:\d{2})$/.test(value)?value+'Z':value);
  if(Number.isNaN(instant.getTime()))return 'Unavailable';
  return new Intl.DateTimeFormat('en-IN', {timeZone:'Asia/Kolkata', ...(date ? {day:'2-digit',month:'short',year:'numeric'} as const : {}), hour:'2-digit',minute:'2-digit', ...(date ? {} : {second:'2-digit'} as const), hour12:false}).format(instant);
}
export function indiaDay(value:Date|string=new Date()):string {
  return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value));
}
export function shiftDay(day:string,offset:number):string {
  return new Date(new Date(day+'T12:00:00Z').getTime()+offset*86400000).toISOString().slice(0,10);
}
export function duration(value:number|null|undefined):string {
  if (value == null) return 'Unavailable';
  const seconds = Math.round(value);
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds/60)}m ${seconds%60}s`;
}
export function label(value:string):string { return value.toLowerCase().replaceAll('_',' '); }
export function dateBoundary(date:string, next=false):string {
  const dt = new Date(`${date}T00:00:00+05:30`);
  if (next) dt.setTime(dt.getTime()+86400000);
  return dt.toISOString();
}
export async function api<T>(path:string, init?:RequestInit):Promise<T> {
  const response = await fetch(`/api/v1${path}`, {credentials:'same-origin', ...init, headers:{'Content-Type':'application/json','X-CSRF-Protection':'1', ...init?.headers}});
  if (!response.ok) {
    if(response.status===401 && !path.startsWith('/auth/') && typeof window!=='undefined') {
      window.dispatchEvent(new Event('session-expired'));
    }
    const body = await response.json().catch(()=>({detail:response.statusText}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status})`);
  }
  return response.json();
}
