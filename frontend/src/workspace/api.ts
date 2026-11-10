export type Row = Record<string, any>;
export type Profile = {username:string;role:string;active:boolean};
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
export const money=(value:any)=>value===null||value===undefined?'Chưa cấu hình':Number(value).toLocaleString('vi-VN')+' ₫';
export const date=(value:any)=>value?new Date(value.endsWith?.('Z')?value:value+'Z').toLocaleString('vi-VN'):'—';
export function go(role:string,page='home'){window.location.hash=`/${role}/${page}`;}
export const roleConfig:Record<string,{title:string;label:string;accent:string;subtitle:string}>= {
 ADMIN:{title:'Quản trị hệ thống',label:'Admin',accent:'#8b5cf6',subtitle:'Danh tính · Danh mục · Kiểm soát truy cập'},
 SOC_MANAGER:{title:'Trung tâm điều hành',label:'SOC Manager',accent:'#3b82f6',subtitle:'Rủi ro tổ chức · Hiệu suất · Phân công'},
 SOC_L1:{title:'Hàng đợi phân loại',label:'SOC Analyst L1',accent:'#06b6d4',subtitle:'Phát hiện sớm · Ưu tiên SLA · Chuyển cấp'},
 SOC_L2:{title:'Bàn điều tra',label:'SOC Analyst L2',accent:'#f59e0b',subtitle:'Bằng chứng · Tương quan IOC · Khoanh vùng'},
 SOC_L3:{title:'Phòng phân tích chuyên sâu',label:'SOC Analyst L3',accent:'#ec4899',subtitle:'Critical / High · Kỹ thuật tấn công · Phân tích'},
 INCIDENT_RESPONDER:{title:'Trung tâm ứng phó',label:'Incident Responder',accent:'#f97316',subtitle:'Cô lập · Khắc phục · Phục hồi'},
 THREAT_HUNTER:{title:'Không gian săn mối đe dọa',label:'Threat Hunter',accent:'#10b981',subtitle:'IOC · MITRE ATT&CK · Phát hiện mới'},
};
