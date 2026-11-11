import {useEffect,useState} from 'react';
import {api,post} from '../../shared/api/client';
import {Row} from '../../shared/types';

export function useIncidentDetail(token:string,id:string){
 const [data,setData]=useState<Row|null>(null),[intel,setIntel]=useState<Row>({iocs:[],techniques:[]}),[error,setError]=useState('');
 const [assignmentRole,setAssignmentRole]=useState('SOC_L2');
 const load=async()=>{try{const [d,i]=await Promise.all([api(token,'/workspace/incidents/'+id),api(token,'/workspace/intelligence')]);setData(d);setIntel(i);setError('')}catch(e:any){setError(e.message)}};
 useEffect(()=>{setData(null);load()},[id,token]);
 const mutate=async(path:string,body:Row,method='POST')=>{const r=await post(token,`/workspace/incidents/${id}/${path}`,body,method);await load();return r};

 return {data,intel,error,assignmentRole,setAssignmentRole,load,mutate};
}
