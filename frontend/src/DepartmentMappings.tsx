import { useState } from 'react';
import { useMutation,useQuery,useQueryClient } from '@tanstack/react-query';
import { api,localTime } from './lib';

type Mapping={id:number;source_type:string;source_value:string;department:string;effective_from:string;effective_to:string|null};

export function DepartmentMappings(){
  const cache=useQueryClient();
  const list=useQuery({queryKey:['department-mappings'],queryFn:()=>api<{items:Mapping[]}>('/admin/department-mappings')});
  const [kind,setKind]=useState('DID');const [value,setValue]=useState('');const [department,setDepartment]=useState('');const [from,setFrom]=useState('');
  const create=useMutation({mutationFn:()=>api('/admin/department-mappings',{method:'POST',body:JSON.stringify({source_type:kind,source_value:value,department,effective_from:new Date(from+'+05:30').toISOString()})}),onSuccess:()=>{setValue('');setDepartment('');cache.invalidateQueries();}});
  const end=useMutation({mutationFn:(id:number)=>api(`/admin/department-mappings/${id}/end`,{method:'POST'}),onSuccess:()=>cache.invalidateQueries()});
  return <section className="panel admin-panel"><h2>Department mappings</h2><p className="muted">Assign a DID or provider department name to your internal department. The effective date determines which calls are attributed. No provider routing is changed.</p><div className="table-wrap"><table><thead><tr><th>Source</th><th>Department</th><th>Effective · IST</th><th>Action</th></tr></thead><tbody>{list.data?.items.map(m=><tr key={m.id}><td>{m.source_type}<small>{m.source_value}</small></td><td>{m.department}</td><td>{localTime(m.effective_from,true)}<small>{m.effective_to?`Ended ${localTime(m.effective_to,true)}`:'Active'}</small></td><td>{!m.effective_to && <button className="text-button" disabled={end.isPending} onClick={()=>end.mutate(m.id)}>End mapping</button>}</td></tr>)}</tbody></table></div><form className="staff-form" onSubmit={e=>{e.preventDefault();create.mutate();}}><label>Source type<select value={kind} onChange={e=>setKind(e.target.value)}><option value="DID">DID number</option><option value="DEPARTMENT">Provider department name</option></select></label><label>Exact source value<input value={value} onChange={e=>setValue(e.target.value)} required maxLength={120}/></label><label>Internal department<input value={department} onChange={e=>setDepartment(e.target.value)} required maxLength={120}/></label><label>Effective from · IST<input type="datetime-local" value={from} onChange={e=>setFrom(e.target.value)} required/></label><button className="primary" disabled={create.isPending}>Add mapping</button></form>{(create.error||end.error||list.error) && <p className="notice error">{(create.error||end.error||list.error)?.message}</p>}</section>;
}
