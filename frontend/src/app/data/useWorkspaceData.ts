import {useEffect,useState} from 'react';
import {api} from '../../shared/api/client';
import {Row,Profile} from '../../shared/types';

export function useWorkspaceState(){
 const [roles,setRoles]=useState<Row[]>([]),[staff,setStaff]=useState<Row[]>([]),[incidents,setIncidents]=useState<Row[]>([]),[reports,setReports]=useState<Row>({});
 const [month,setMonth]=useState(()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`});
 const [error,setError]=useState(''),[loading,setLoading]=useState(true),[version,setVersion]=useState(0),[audit,setAudit]=useState<Row[]>([]);
 return {roles,setRoles,staff,setStaff,incidents,setIncidents,reports,setReports,month,setMonth,error,setError,loading,setLoading,version,setVersion,audit,setAudit};
}

export type WorkspaceState=ReturnType<typeof useWorkspaceState>;

export function useWorkspaceData(token:string,profile:Profile|null,route:string[],state:WorkspaceState){
 const {roles,setRoles,staff,setStaff,incidents,setIncidents,reports,setReports,month,setMonth,error,setError,loading,setLoading,version,setVersion,audit,setAudit}=state;
 useEffect(()=>{if(!token||!profile)return;let active=true;setLoading(true);setError('');
  Promise.all([api(token,'/roles'),api(token,'/workspace/staff'),profile.role==='ADMIN'?Promise.resolve([]):api(token,'/workspace/incidents'),profile.role==='ADMIN'?Promise.resolve({}):api(token,'/workspace/reports?month='+month)])
  .then(([r,s,i,p])=>{if(active){setRoles(r);setStaff(s);setIncidents(i);setReports(p)}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false};
 },[token,profile?.role,month,version]);
 useEffect(()=>{if(profile?.role==='ADMIN'&&route[1]==='audit')api(token,'/workspace/audit').then(setAudit).catch(e=>setError(e.message))},[route.join('/'),token,profile?.role,version]);
}
