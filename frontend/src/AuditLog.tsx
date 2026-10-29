import { PageSize,usePageSize,pageSizeQuery } from './PageSize';
import { useState,useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api,localTime,label } from './lib';

export function AuditLog(){
  const [page,setPage]=useState(1);const size=usePageSize();useEffect(()=>setPage(1),[size]);
  const query=useQuery({queryKey:['audit',page,size],queryFn:()=>api<{items:{at:string;actor:string;role:string;action:string;resource:string}[];next_page:number|null}>(`/admin/audit?page=${page}&${pageSizeQuery(size)}`)});
  return <section className="panel admin-panel"><h2>Access and administration log</h2><p className="muted">Named-account audit entries for exports, access denials, passwords and administration.</p><div className="table-wrap"><table><thead><tr><th>Time · IST</th><th>Account</th><th>Action</th><th>Resource</th></tr></thead><tbody>{query.data?.items.map((row,i)=><tr key={i}><td>{localTime(row.at,true)}</td><td>{row.actor}<small>{row.role}</small></td><td>{label(row.action)}</td><td>{row.resource}</td></tr>)}</tbody></table></div>{query.error && <p className="notice error">{query.error.message}</p>}<div className="pagination"><span>Page {page}</span><PageSize onChange={()=>setPage(1)}/><div><button className="text-button" disabled={page===1} onClick={()=>setPage(page-1)}>Previous</button><button className="text-button" disabled={!query.data?.next_page} onClick={()=>setPage(page+1)}>Next</button></div></div></section>;
}
