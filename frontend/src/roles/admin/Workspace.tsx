import './ui2.css';
import {RoleTabs} from '../../shared/components/RoleTabs';
import Accounts from './Accounts';
import {useEffect,useState} from 'react';
import {api,post,allRows} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {go} from '../../app/routing/navigation';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {Stats} from '../../shared/components/Stats';
import {ActionForm} from '../../shared/forms/ActionForm';
import {Select} from '../../shared/forms/fields';

export function AdminLayout({token,roles,staff,reload}:{token:string;roles:any[];staff:Row[];reload:()=>void}){
 const [employees,setEmployees]=useState<Row[]>([]),[accounts,setAccounts]=useState<Row[]>([]);
 const [error,setError]=useState('');
 const [tab,setTab]=useState('overview');
 const load=()=>Promise.all([allRows(token,'nhan_vien_soc'),api(token,'/accounts')]).then(([e,a])=>{setEmployees(e);setAccounts(a)}).catch(e=>setError(e.message));
 useEffect(()=>{load()},[token]);
 return <div className="admin-layout ui2-admin"><div className="ui2-heading"><span>QUẢN TRỊ HỆ THỐNG</span><h2>Danh tính, con người & tài nguyên</h2><p>Quản lý truy cập và danh mục từ một không gian thống nhất.</p></div><RoleTabs idPrefix="admin" label="Khu vực quản trị" value={tab} onChange={setTab} items={[{id:'overview',label:'Tổng quan'},{id:'accounts',label:'Tài khoản'},{id:'roles',label:'Vai trò & phân quyền'},{id:'profiles',label:'Liên kết nhân viên'}]}/><div className="admin-overview" id="admin-panel-overview" role="tabpanel" aria-labelledby="admin-overview" hidden={tab!=='overview'}><Stats items={[{label:'Tài khoản',value:accounts.length},{label:'Đang hoạt động',value:accounts.filter(a=>a.active).length},{label:'Vai trò',value:roles.length}]}/><Panel title="Danh mục hệ thống"><div className="admin-shortcuts">{[['to_chuc','Tổ chức'],['tai_san','Tài sản CNTT'],['nhan_vien_soc','Nhân viên SOC'],['audit','Nhật ký hoạt động']].map(([page,label])=><button className="w-shortcut" key={page} onClick={()=>go('ADMIN',page)}><strong>{label}</strong><span>Mở khu vực quản lý →</span></button>)}</div></Panel></div><div hidden={!['accounts','roles'].includes(tab)}><Accounts token={token} roles={roles} onChange={load} view={tab==='roles'?'roles':'accounts'} onViewAccounts={()=>setTab('accounts')}/></div>
 <aside id="admin-panel-profiles" role="tabpanel" aria-labelledby="admin-profiles" hidden={tab!=='profiles'}><Panel title="Liên kết tài khoản – nhân viên">{error&&<div className="error-box">{error}</div>}<p>Liên kết để xác định dữ liệu “Của tôi” và người thực hiện hành động.</p><ActionForm label="Lưu liên kết" onSubmit={async d=>{const r=await post(token,'/workspace/profiles/'+encodeURIComponent(String(d.get('username'))),{employee_id:d.get('employee_id')},'PUT');await load();reload();return r;}}><Select label="Tài khoản" name="username" options={accounts.filter(a=>a.role!=='ADMIN').map(a=>({value:a.username,label:a.username+' · '+a.role}))}/><Select label="Nhân viên SOC" name="employee_id" options={employees.map(e=>({value:e.MaNV,label:e.HoTen+' · '+e.MaNV}))}/></ActionForm><DataTable rows={staff} columns={[{key:'username',label:'Tài khoản'},{key:'employee_id',label:'Mã NV'},{key:'role',label:'Vai trò'}]}/></Panel><div className="workspace-note">Khu vực quản trị danh mục và danh tính. Các thao tác xử lý Incident thuộc khu vực nghiệp vụ.</div></aside></div>;
}
