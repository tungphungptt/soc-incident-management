import {Modal} from '../../shared/components/Modal';
import {Button} from '../../shared/components/Button';
import {DataTable} from '../../shared/components/DataTable';
import {searchText} from '../../shared/search';
import React from 'react';
import {useEffect,useState} from 'react';

export type Role = {id:string;label:string;description:string};

export type Account = {username:string;role:string;active:boolean};

export default function Accounts({token,roles,onChange,view='accounts',onViewAccounts}:{token:string;roles:Role[];onChange?:()=>void;view?:'accounts'|'roles';onViewAccounts?:()=>void}) {
 const [open,setOpen]=useState(false),[query,setQuery]=useState(''),[roleFilter,setRoleFilter]=useState(''),[status,setStatus]=useState('');
 const close=()=>{if(!busy){setOpen(false);setEditing(null);setUsername('');setPassword('');setError('');}};
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
   setEditing(null);setUsername('');setPassword('');await load();onChange?.();setOpen(false);
  }catch(e:any){setError(e.message);}finally{setBusy(false);}
 };
 const filtered=accounts.filter(a=>(!query||searchText(a.username+' '+(roles.find(r=>r.id===a.role)?.label||a.role)).includes(searchText(query)))&&(!roleFilter||a.role===roleFilter)&&(!status||Boolean(a.active)===(status==='active')));
 return <section className="panel ui2-accounts">
 <div id="admin-panel-accounts" role="tabpanel" aria-labelledby="admin-accounts" hidden={view!=='accounts'}><div className="panel-head"><div><h2>Tài khoản và phân quyền</h2><p>Kiểm soát danh tính, vai trò và trạng thái truy cập.</p></div><Button variant="primary" onClick={()=>{setEditing(null);setUsername('');setPassword('');setError('');setOpen(true);}}>Thêm tài khoản</Button></div>
 {!open&&error&&<div className="error-box" role="alert">{error}</div>}
 <div className="ui2-filters"><label>Tìm tài khoản<input type="search" placeholder="Tên đăng nhập hoặc vai trò…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Vai trò<select aria-label="Vai trò" value={roleFilter} onChange={e=>setRoleFilter(e.target.value)}><option value="">Tất cả vai trò</option>{roles.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label><label>Trạng thái<select aria-label="Trạng thái" value={status} onChange={e=>setStatus(e.target.value)}><option value="">Tất cả trạng thái</option><option value="active">Hoạt động</option><option value="locked">Đã khóa</option></select></label></div>
 <p className="ui2-result-count">{filtered.length} / {accounts.length} tài khoản</p>
 <div className="table-wrap ui2-accounts-table"><DataTable rows={filtered} columns={[{key:'username',label:'Tài khoản'},{key:'role',label:'Vai trò',render:a=>roles.find(r=>r.id===a.role)?.label||a.role},{key:'active',label:'Trạng thái',render:a=><span className={a.active?'ui2-status active':'ui2-status'}>{a.active?'Hoạt động':'Đã khóa'}</span>},{key:'actions',label:'Thao tác',render:a=><Button variant="secondary" onClick={()=>{setEditing({...a} as Account);setUsername(a.username);setPassword('');setRole(a.role);setError('');setOpen(true);}}>Chỉnh sửa</Button>}]}/></div></div>
 <div id="admin-panel-roles" role="tabpanel" aria-labelledby="admin-roles" hidden={view!=='roles'}><div className="panel-head"><div><h2>Vai trò & phân quyền</h2><p>Phạm vi chức năng theo cấu hình hệ thống. Quyền được kiểm soát tại backend.</p></div></div><div className="ui2-role-cards">{roles.map(r=><article key={r.id}><span className="ui2-role-code">{r.id}</span><h3>{r.label}</h3><p>{r.description}</p><Button variant="secondary" onClick={()=>{setRoleFilter(r.id);setQuery('');setStatus('');onViewAccounts?.();}}>Xem tài khoản ({accounts.filter(a=>a.role===r.id).length})</Button></article>)}</div></div>
 {open&&<Modal title={editing?'Chỉnh sửa tài khoản':'Tạo tài khoản'} onClose={close}>{error&&<div className="error-box" role="alert">{error}</div>}
  <form onSubmit={save} className="account-form ui2-account-form"><div className="form-grid">
 <div className="field"><label htmlFor="account-name">Tên đăng nhập</label><input id="account-name" value={username} disabled={!!editing} onChange={e=>setUsername(e.target.value)} required autoComplete="off"/></div>
 <div className="field"><label htmlFor="account-password">{editing?'Mật khẩu mới (để trống để giữ nguyên)':'Mật khẩu (ít nhất 10 ký tự)'}</label><input id="account-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={10} required={!editing} autoComplete="new-password"/></div>
 <div className="field"><label htmlFor="account-role">Vai trò</label><select id="account-role" value={role} onChange={e=>setRole(e.target.value)}>{roles.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></div>
 {editing&&<label><input type="checkbox" checked={editing.active} onChange={e=>setEditing({...editing,active:e.target.checked})}/> Đang hoạt động</label>}
 </div><div className="modal-actions"><Button variant="secondary" onClick={close} disabled={busy}>Hủy</Button><Button type="submit" variant="primary" disabled={busy}>{busy?'Đang lưu…':editing?'Lưu thay đổi':'Tạo tài khoản'}</Button></div></form></Modal>}</section>;
}
