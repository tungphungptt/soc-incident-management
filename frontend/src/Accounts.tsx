import React, { useEffect, useState } from 'react';

export type Role = {id:string;label:string;description:string};
type Account = {username:string;role:string;active:boolean};

export default function Accounts({token,roles,onChange}:{token:string;roles:Role[];onChange?:()=>void}) {
 const [accounts,setAccounts]=useState<Account[]>([]);
 const [username,setUsername]=useState('');
 const [password,setPassword]=useState('');
 const [role,setRole]=useState('SOC_L1');
 const [error,setError]=useState('');
 const [busy,setBusy]=useState(false);
 const [editing,setEditing]=useState<Account|null>(null);
 const api=async(path:string,init:RequestInit={})=>{
  const res=await fetch((import.meta.env.VITE_API_BASE_URL||'/api/v1')+path,{...init,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`}});
  const data=await res.json();if(!res.ok)throw new Error(typeof data.detail==='string'?data.detail:'Kiểm tra lại thông tin tài khoản');return data;
 };
 const load=async()=>setAccounts(await api('/accounts'));
 useEffect(()=>{load().catch(e=>setError(e.message));},[token]);
 const save=async(e:React.FormEvent)=>{
  e.preventDefault();setBusy(true);setError('');
  try{
   await api(editing?`/accounts/${encodeURIComponent(editing.username)}`:'/accounts',{method:editing?'PUT':'POST',body:JSON.stringify(editing?{role,active:editing.active,...(password?{password}:{})}:{username,password,role})});
   setEditing(null);setUsername('');setPassword('');await load();onChange?.();
  }catch(e:any){setError(e.message);}finally{setBusy(false);}
 };
 return <section className="panel"><div className="panel-head"><div><h2>Tài khoản và phân quyền</h2><p>Tạo tài khoản và chọn vai trò cho từng người dùng.</p></div></div>
 {error&&<div className="error-box" role="alert">{error}</div>}
 <form onSubmit={save} className="account-form"><div className="form-grid">
 <div className="field"><label htmlFor="account-name">Tên đăng nhập</label><input id="account-name" value={username} disabled={!!editing} onChange={e=>setUsername(e.target.value)} required autoComplete="off"/></div>
 <div className="field"><label htmlFor="account-password">{editing?'Mật khẩu mới (để trống để giữ nguyên)':'Mật khẩu (ít nhất 10 ký tự)'}</label><input id="account-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={10} required={!editing} autoComplete="new-password"/></div>
 <div className="field"><label htmlFor="account-role">Vai trò</label><select id="account-role" value={role} onChange={e=>setRole(e.target.value)}>{roles.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></div>
 {editing&&<label><input type="checkbox" checked={editing.active} onChange={e=>setEditing({...editing,active:e.target.checked})}/> Đang hoạt động</label>}
 </div><div className="modal-actions">{editing&&<button type="button" className="secondary" onClick={()=>{setEditing(null);setUsername('');setPassword('');}}>Hủy</button>}<button className="primary" disabled={busy}>{busy?'Đang lưu…':editing?'Lưu thay đổi':'Tạo tài khoản'}</button></div></form>
 <div className="table-wrap"><table><thead><tr><th>Tài khoản</th><th>Vai trò</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{accounts.map(a=><tr key={a.username}><td>{a.username}</td><td>{roles.find(r=>r.id===a.role)?.label||a.role}</td><td>{a.active?'Hoạt động':'Đã khóa'}</td><td><button className="secondary" onClick={()=>{setEditing({...a});setUsername(a.username);setPassword('');setRole(a.role);}}>Chỉnh sửa</button></td></tr>)}</tbody></table></div>
 <div className="role-grid">{roles.map(r=><div className="note" key={r.id}><div><b>{r.label}</b><p>{r.description}</p></div></div>)}</div>
 </section>;
}
