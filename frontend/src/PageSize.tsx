import { useSyncExternalStore } from 'react';
import { useSearchParams } from 'react-router-dom';
const options=['10','25','50','100','all'];
function snapshot(){try{const value=localStorage.getItem('twss-page-size')||'10';return options.includes(value)?value:'10';}catch{return '10';}}
function subscribe(callback:()=>void){window.addEventListener('twss-page-size',callback);window.addEventListener('storage',callback);return()=>{window.removeEventListener('twss-page-size',callback);window.removeEventListener('storage',callback);};}
export function usePageSize(){return useSyncExternalStore(subscribe,snapshot,()=> '10');}
export function pageSizeQuery(value:string){return `page_size=${value==='all'?'100':value}&show_all=${value==='all'}`;}
export function PageSize({onChange}:{onChange?:()=>void}){
  const size=usePageSize();const [params,setParams]=useSearchParams();
  return <label className="page-size-control">Rows per page<select aria-label="Rows per page" value={size} onChange={e=>{const next=new URLSearchParams(params);next.delete('page');next.delete('page_size');next.delete('show_all');setParams(next);try{localStorage.setItem('twss-page-size',e.target.value);}catch{/* Browser storage may be disabled. */}window.dispatchEvent(new Event('twss-page-size'));onChange?.();}}>{options.map(value=><option key={value} value={value}>{value==='all'?'All':value}</option>)}</select></label>;
}
