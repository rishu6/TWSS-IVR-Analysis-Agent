import { Brand } from './Brand';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ArrowRight, ShieldCheck, Workflow } from 'lucide-react';
import { api } from './lib';

export function InternalLogin({onLogin}:{onLogin:()=>void}) {
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const login=useMutation({mutationFn:()=>api('/auth/login',{method:'POST',body:JSON.stringify({username,password})}),onSuccess:onLogin});
  return <main className="login-page"><div className="login-story"><Brand/><span className="eyebrow">TWSS INTERNAL WORKSPACE</span><h1>Every call.<br/>A clearer picture.</h1><p>Acefone India call history<br/>and LeadSquared customer context.</p></div><form className="login-card" onSubmit={e=>{e.preventDefault();login.mutate();}}><span className="pill">STAFF ACCESS</span><h2>Sign in to your account</h2><p>Use the individual account supplied by your administrator.</p><label>Username<input autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} required autoFocus/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required maxLength={256}/></label>{login.error && <div className="notice error" role="alert">{login.error.message}</div>}<button className="primary" disabled={login.isPending}>Sign in <ArrowRight size={17}/></button><p className="fine"><ShieldCheck size={15}/> Access is limited to approved staff. Contact your administrator if you cannot sign in.</p></form></main>;
}

export function ChangePassword({onChanged,onCancel}:{onChanged:()=>void;onCancel?:()=>void}) {
  const [current,setCurrent]=useState(''); const [password,setPassword]=useState(''); const [confirm,setConfirm]=useState('');
  const change=useMutation({mutationFn:()=>api('/auth/change-password',{method:'POST',body:JSON.stringify({current_password:current,new_password:password})}),onSuccess:onChanged});
  return <main className="login-page"><div className="login-story"><h1>Make your<br/>account yours.</h1><p>Replace the temporary password before accessing customer data.</p></div><form className="login-card" onSubmit={e=>{e.preventDefault();if(password===confirm)change.mutate();}}><h2>Set your password</h2><label>Temporary / current password<input type="password" autoComplete="current-password" value={current} onChange={e=>setCurrent(e.target.value)} required/></label><label>New password · at least 12 characters<input type="password" autoComplete="new-password" minLength={12} maxLength={256} value={password} onChange={e=>setPassword(e.target.value)} required/></label><label>Confirm new password<input type="password" autoComplete="new-password" value={confirm} onChange={e=>setConfirm(e.target.value)} required/></label>{confirm && password!==confirm && <p className="notice">Passwords must match.</p>}{change.error && <div className="notice error" role="alert">{change.error.message}</div>}<button className="primary" disabled={change.isPending||password!==confirm}>Save password and continue</button>{onCancel && <button type="button" className="text-button" onClick={onCancel}>Cancel</button>}</form></main>;
}
