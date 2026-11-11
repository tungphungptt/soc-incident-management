import {Row} from '../types';

export async function api(token:string,path:string,init:RequestInit={}) {
 const response=await fetch((import.meta.env.VITE_API_BASE_URL||'/api/v1')+path,{...init,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`,...init.headers}});
 const data=await response.json().catch(()=>({}));
 if(!response.ok){
  if(response.status===401)window.dispatchEvent(new Event('soc-session-expired'));
  const detail=data.detail;
  throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.map(x=>x.msg).join('; '):detail?.unknown_fields?'Trường không hợp lệ: '+detail.unknown_fields.join(', '):`Yêu cầu không thành công (${response.status}).`);
 }
 return data;
}

export const post=(token:string,path:string,body:Row,method='POST')=>api(token,path,{method,body:JSON.stringify(body)});

export async function allRows(token:string,table:string):Promise<Row[]>{
 const first=await api(token,`/tables/${table}?page_size=100&page=1`);
 const result:Row[]=[...first.items];
 for(let page=2;page<=Math.ceil(first.total/100);page++){
  const data=await api(token,`/tables/${table}?page_size=100&page=${page}`);result.push(...data.items);
 }
 return result;
}
