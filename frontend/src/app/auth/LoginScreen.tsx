import React from 'react';
import {Shield} from 'lucide-react';
import {Authentication} from './useAuthentication';

export function LoginScreen({auth,error,themeButton}:{auth:Authentication;error:string;themeButton:React.ReactNode}){
 const {login,loginUser,setLoginUser,loginPass,setLoginPass,loginBusy}=auth;
 return <div className="login-screen"><div className="login-theme">{themeButton}</div><div className="login-card"><div className="brand-mark"><Shield size={27}/></div><div className="eyebrow">SOC OPERATIONS PLATFORM</div><h1>Đăng nhập SOC</h1><p className="muted">Khu vực làm việc riêng cho từng vai trò.</p><form onSubmit={login}><label htmlFor="login-user">Tên đăng nhập</label><input id="login-user" autoComplete="username" value={loginUser} onChange={e=>setLoginUser(e.target.value)} required/><label htmlFor="login-password">Mật khẩu</label><input id="login-password" type="password" autoComplete="current-password" value={loginPass} onChange={e=>setLoginPass(e.target.value)} required/>{error&&<div className="error-box" role="alert">{error}</div>}<button className="primary wide" disabled={loginBusy}>{loginBusy?'Đang đăng nhập…':'Vào khu vực làm việc →'}</button></form></div></div>;
}
