import React,{useEffect,useState} from 'react';
import {Shield,Sun,Moon,LogOut,RefreshCw,LayoutDashboard,ClipboardList,UserRound,Building2,Monitor,Users,History,Fingerprint} from 'lucide-react';
import {api,Profile,Row,roleConfig,go,date} from './workspace/api';
import {Panel,DataTable,IncidentTable} from './workspace/components';
import {Directory} from './workspace/forms';
import IncidentDetail from './workspace/IncidentDetail';
import {AdminLayout,ManagerLayout,AnalystL1Layout,AnalystL2Layout,AnalystL3Layout,ResponderLayout,HunterLayout,Personal,WorkspaceProps} from './workspace/layouts';
import './workspace/workspace.css';

function useRoute(){const [route,setRoute]=useState(location.hash.slice(2).split('/'));useEffect(()=>{const change=()=>setRoute(location.hash.slice(2).split('/'));window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change)},[]);return route;}

export default function App(){
 const [theme,setTheme]=useState<'light'|'dark'>(()=>localStorage.getItem('soc_theme')==='light'?'light':'dark');
 const [token,setToken]=useState(localStorage.getItem('soc_token')||''),[profile,setProfile]=useState<Profile|null>(null);
 const [roles,setRoles]=useState<Row[]>([]),[staff,setStaff]=useState<Row[]>([]),[incidents,setIncidents]=useState<Row[]>([]),[reports,setReports]=useState<Row>({});
 const [month,setMonth]=useState(()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`});
 const [error,setError]=useState(''),[loading,setLoading]=useState(true),[version,setVersion]=useState(0),[audit,setAudit]=useState<Row[]>([]);
 const [loginUser,setLoginUser]=useState(''),[loginPass,setLoginPass]=useState(''),[loginBusy,setLoginBusy]=useState(false);
 const route=useRoute();
 const logout=()=>{localStorage.removeItem('soc_token');setToken('');setProfile(null);setIncidents([]);setReports({});setStaff([]);setError('');setLoading(true);location.hash='';};
 useEffect(()=>{document.documentElement.dataset.theme=theme;localStorage.setItem('soc_theme',theme)},[theme]);
 useEffect(()=>{window.addEventListener('soc-session-expired',logout);return()=>window.removeEventListener('soc-session-expired',logout)},[]);
 useEffect(()=>{if(!token)return;let active=true;api(token,'/auth/me').then(p=>{if(active){setProfile(p);if(!location.hash||location.hash==='#')go(p.role)}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[token,version]);
 useEffect(()=>{if(!token||!profile)return;let active=true;setLoading(true);setError('');
  Promise.all([api(token,'/roles'),api(token,'/workspace/staff'),profile.role==='ADMIN'?Promise.resolve([]):api(token,'/workspace/incidents'),profile.role==='ADMIN'?Promise.resolve({}):api(token,'/workspace/reports?month='+month)])
  .then(([r,s,i,p])=>{if(active){setRoles(r);setStaff(s);setIncidents(i);setReports(p)}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false};
 },[token,profile?.role,month,version]);
 useEffect(()=>{if(profile?.role==='ADMIN'&&route[1]==='audit')api(token,'/workspace/audit').then(setAudit).catch(e=>setError(e.message))},[route.join('/'),token,profile?.role,version]);
 const themeButton=<button type="button" className="theme-toggle" onClick={()=>setTheme(t=>t==='dark'?'light':'dark')} aria-label="Chuyển giao diện sáng tối">{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>} {theme==='dark'?'Sáng':'Tối'}</button>;
 if(!token)return <div className="login-screen"><div className="login-theme">{themeButton}</div><div className="login-card"><div className="brand-mark"><Shield size={27}/></div><div className="eyebrow">SOC OPERATIONS PLATFORM</div><h1>Đăng nhập SOC</h1><p className="muted">Khu vực làm việc riêng cho từng vai trò.</p><form onSubmit={async e=>{e.preventDefault();setLoginBusy(true);setError('');try{const r=await api('', '/auth/login',{method:'POST',body:JSON.stringify({username:loginUser,password:loginPass})});localStorage.setItem('soc_token',r.access_token);setProfile(r.user);setToken(r.access_token);setLoginPass('');go(r.user.role)}catch(e:any){setError(e.message)}finally{setLoginBusy(false)}}}><label htmlFor="login-user">Tên đăng nhập</label><input id="login-user" autoComplete="username" value={loginUser} onChange={e=>setLoginUser(e.target.value)} required/><label htmlFor="login-password">Mật khẩu</label><input id="login-password" type="password" autoComplete="current-password" value={loginPass} onChange={e=>setLoginPass(e.target.value)} required/>{error&&<div className="error-box" role="alert">{error}</div>}<button className="primary wide" disabled={loginBusy}>{loginBusy?'Đang đăng nhập…':'Vào khu vực làm việc →'}</button></form></div></div>;
 if(!profile)return <div className="login-screen">{error||'Đang kiểm tra phiên đăng nhập…'}<button className="secondary" onClick={logout}>Đăng nhập lại</button></div>;
 const config=roleConfig[profile.role];if(!config)return <div className="error-box">Vai trò không được hỗ trợ.<button onClick={logout}>Đăng xuất</button></div>;
 const reload=()=>setVersion(v=>v+1),admin=profile.role==='ADMIN';
 const menu=admin?[{page:'home',label:'Tài khoản & phân quyền',icon:Users},{page:'to_chuc',label:'Tổ chức',icon:Building2},{page:'tai_san',label:'Tài sản CNTT',icon:Monitor},{page:'nhan_vien_soc',label:'Nhân viên SOC',icon:UserRound},{page:'audit',label:'Nhật ký hoạt động',icon:History}]:[{page:'home',label:config.title,icon:LayoutDashboard},{page:'incidents',label:'Hồ sơ Incident',icon:ClipboardList},...(profile.role==='THREAT_HUNTER'?[{page:'intelligence',label:'Tra cứu IOC / MITRE',icon:Fingerprint}]:[]),{page:'personal',label:'Của tôi',icon:UserRound}];
 const page=route[1]||'home';const forbidden=route[0]!==profile.role||!menu.some(m=>m.page===page);
 const props:WorkspaceProps={token,profile,incidents,reports,staff,reload,month};
 let content:React.ReactNode;
 if(forbidden)content=<Panel title="Không có quyền"><p>URL này thuộc khu vực vai trò khác hoặc không tồn tại.</p><button className="primary" onClick={()=>go(profile.role)}>Về trang chủ của tôi</button></Panel>;
 else if(page==='personal')content=<Personal token={token} month={month}/>;
 else if(admin&&['to_chuc','tai_san','nhan_vien_soc'].includes(page))content=<Directory key={page} token={token} table={page}/>;
 else if(page==='audit')content=<Panel title="Nhật ký hoạt động"><DataTable rows={audit} columns={[{key:'created_at',label:'Thời điểm',render:r=>date(r.created_at)},{key:'username',label:'Người thực hiện'},{key:'action',label:'Hành động'},{key:'target',label:'Đối tượng'},{key:'detail',label:'Chi tiết'}]}/></Panel>;
 else if(page==='incidents'&&route[2])content=<IncidentDetail token={token} profile={profile} id={route[2]} staff={staff}/>;
 else if(page==='incidents')content=<Panel title={['SOC_L2','INCIDENT_RESPONDER'].includes(profile.role)?'Incident được giao cho tôi':'Tra cứu hồ sơ Incident'}><IncidentTable rows={incidents} role={profile.role}/></Panel>;
 else if(admin)content=<AdminLayout token={token} roles={roles} staff={staff} reload={reload}/>;
 else if(profile.role==='SOC_MANAGER')content=<ManagerLayout {...props}/>;
 else if(profile.role==='SOC_L1')content=<AnalystL1Layout {...props}/>;
 else if(profile.role==='SOC_L2')content=<AnalystL2Layout {...props}/>;
 else if(profile.role==='SOC_L3')content=<AnalystL3Layout {...props}/>;
 else if(profile.role==='INCIDENT_RESPONDER')content=<ResponderLayout {...props}/>;
 else content=<HunterLayout {...props}/>;
 return <div className="role-workspace" data-role={profile.role} style={{'--accent':config.accent} as React.CSSProperties}>
 <aside className="workspace-sidebar"><div className="workspace-brand"><Shield/><b>SOC<span>OPS</span></b></div><div className="workspace-role"><small>KHU VỰC LÀM VIỆC</small><strong>{config.label}</strong><span>{config.subtitle}</span></div><nav>{menu.map(m=><button key={m.page} className={`workspace-nav ${page===m.page&&!forbidden?'active':''}`} onClick={()=>go(profile.role,m.page)}><m.icon size={18}/>{m.label}</button>)}</nav><div className="workspace-user"><div className="workspace-user-avatar">{profile.username[0].toUpperCase()}</div><div><b>{profile.username}</b><small>{config.label}</small></div><button aria-label="Đăng xuất" className="icon-btn" onClick={logout}><LogOut size={17}/></button></div></aside>
 <main className="workspace-main"><header className="workspace-header"><div><span className="workspace-header-role">{config.label}</span><span className="header-username">{profile.username}</span></div><div className="w-inline">{!admin&&<label className="month-control">Tháng báo cáo<input aria-label="Tháng báo cáo" type="month" value={month} onChange={e=>setMonth(e.target.value)}/></label>}{themeButton}<button className="icon-btn" aria-label="Làm mới" onClick={reload}><RefreshCw size={17}/></button></div></header><div className="workspace-content"><div className="workspace-page-head"><div><span className="workspace-kicker">SOC OPS / {config.label.toUpperCase()}</span><h1>{page==='personal'?'Của tôi':page==='home'||page==='intelligence'?config.title:menu.find(m=>m.page===page)?.label||'Không có quyền'}</h1><p>{page==='personal'?'Thống kê xử lý và thu nhập của chính bạn.':config.subtitle}</p></div><span className="workspace-status"><i/> {loading?'Đang đồng bộ':'Dữ liệu từ hệ thống'}</span></div>{error&&<div className="error-banner" role="alert">{error}</div>}{loading?<div className="w-empty">Đang tải khu vực làm việc…</div>:content}<footer className="workspace-footer">SOC OPS · {config.label} · {profile.username}</footer></div></main></div>;
}
