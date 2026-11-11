import {useEffect,useState} from 'react';
import type React from 'react';
import {api} from '../../shared/api/client';
import {Profile} from '../../shared/types';
import {requireLogin,requireProfile} from './validation';
import {go} from '../routing/navigation';
import {WorkspaceState} from '../data/useWorkspaceData';

export function useAuthentication(state:WorkspaceState){
 const {setIncidents,setReports,setStaff,setError,setLoading,version}=state;
 const [token,setToken]=useState(localStorage.getItem('soc_token')||''),[profile,setProfile]=useState<Profile|null>(null);
 const [loginUser,setLoginUser]=useState(''),[loginPass,setLoginPass]=useState(''),[loginBusy,setLoginBusy]=useState(false);
 const logout=()=>{localStorage.removeItem('soc_token');setToken('');setProfile(null);setIncidents([]);setReports({});setStaff([]);setError('');setLoading(true);location.hash='';};
 useEffect(()=>{window.addEventListener('soc-session-expired',logout);return()=>window.removeEventListener('soc-session-expired',logout)},[]);
 useEffect(()=>{if(!token)return;let active=true;api(token,'/auth/me').then(value=>{const p=requireProfile(value);if(active){setProfile(p);if(!location.hash||location.hash==='#')go(p.role)}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[token,version]);
 const login: (e:React.FormEvent<HTMLFormElement>)=>Promise<void> = async e=>{e.preventDefault();setLoginBusy(true);setError('');try{const r=requireLogin(await api('', '/auth/login',{method:'POST',body:JSON.stringify({username:loginUser,password:loginPass})}));localStorage.setItem('soc_token',r.access_token);setProfile(r.user);setToken(r.access_token);setLoginPass('');go(r.user.role)}catch(e:any){setError(e.message)}finally{setLoginBusy(false)}};
 return {token,profile,logout,login,loginUser,setLoginUser,loginPass,setLoginPass,loginBusy};
}

export type Authentication=ReturnType<typeof useAuthentication>;
