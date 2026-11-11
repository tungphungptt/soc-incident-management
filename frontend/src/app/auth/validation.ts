import type {Profile} from '../../shared/types';
import {SERVER_UNAVAILABLE} from '../../shared/api/client';

const roles=['ADMIN','SOC_MANAGER','SOC_L1','SOC_L2','SOC_L3','INCIDENT_RESPONDER','THREAT_HUNTER'];
export function requireProfile(value:unknown):Profile{
 const p=value as (Omit<Partial<Profile>,'active'>&{active?:unknown})|null;
 if(!p||typeof p.username!=='string'||!p.username.trim()||typeof p.role!=='string'||!roles.includes(p.role)||(typeof p.active!=='boolean'&&p.active!==1&&p.active!==0))throw new Error(SERVER_UNAVAILABLE);
 return {...p,active:p.active===true||p.active===1} as Profile;
}
export function requireLogin(value:unknown):{access_token:string;user:Profile}{
 const r=value as {access_token?:unknown;user?:unknown}|null;
 if(!r||typeof r.access_token!=='string'||!r.access_token.trim())throw new Error(SERVER_UNAVAILABLE);
 const user=requireProfile(r.user);
 if(!user.active)throw new Error(SERVER_UNAVAILABLE);
 return {access_token:r.access_token,user};
}
