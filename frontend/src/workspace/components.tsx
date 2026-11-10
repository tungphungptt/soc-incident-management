import React, {useEffect,useState} from 'react';
import {Clock, ArrowUpRight, ShieldAlert} from 'lucide-react';
import {Row,date,go} from './api';

export function Panel({title,children,action,className=''}:{title:string;children:React.ReactNode;action?:React.ReactNode;className?:string}){
 return <section className={`w-panel ${className}`}><div className="w-panel-title"><h2>{title}</h2>{action}</div>{children}</section>;
}
export function Badge({value}:{value:string}){return <span className={`w-badge badge-${value?.toLowerCase()}`}>{value||'—'}</span>}
export function SLABadge({incident}:{incident:Row}){
 const [now,setNow]=useState(Date.now());useEffect(()=>{const id=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(id)},[]);
 const s=incident.sla;if(!s)return <span>—</span>;
 const seconds=s.closed?s.remaining_seconds:Math.floor((new Date(s.deadline).getTime()-now)/1000);
 const min=Math.floor(Math.abs(seconds)/60);const text=`${Math.floor(min/60)}h ${min%60}m ${Math.abs(seconds)%60}s`;
 return <span className={`w-sla ${seconds<0?'breached':''}`} title={`Hạn: ${date(s.deadline)}`}><Clock size={12}/>{s.closed?(seconds<0?'Đã vi phạm':'Đóng đúng hạn'):seconds<0?'Quá hạn':'Còn'} {s.closed&&seconds>=0?'':text}<small>Hạn {date(s.deadline)}</small></span>;
}
export function DataTable({rows,columns,empty='Chưa có dữ liệu',onRow}:{rows:Row[];columns:{key:string;label:string;render?:(row:Row)=>React.ReactNode}[];empty?:string;onRow?:(row:Row)=>void}){
 return <div className="w-table-scroll"><table className="w-table"><thead><tr>{columns.map(c=><th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i} onClick={()=>onRow?.(r)} className={onRow?'clickable':''}>{columns.map(c=><td key={c.key}>{c.render?c.render(r):r[c.key]===null||r[c.key]===undefined?'—':typeof r[c.key]==='object'?JSON.stringify(r[c.key]):String(r[c.key])}</td>)}</tr>)}</tbody></table>{!rows.length&&<div className="w-empty">{empty}</div>}</div>;
}
export function IncidentTable({rows,role}:{rows:Row[];role:string}){
 return <DataTable rows={rows} columns={[
 {key:'MaIncident',label:'Incident',render:r=><button className="text-link" onClick={()=>go(role,'incidents/'+r.MaIncident)}>{r.MaIncident}<ArrowUpRight size={13}/></button>},
 {key:'MucDoNghiemTrong',label:'Mức độ',render:r=><Badge value={r.MucDoNghiemTrong}/>},
 {key:'TrangThai',label:'Trạng thái',render:r=><Badge value={r.TrangThai}/>},
 {key:'sla',label:'Đồng hồ SLA',render:r=><SLABadge incident={r}/>},
 {key:'assignees',label:'Phụ trách',render:r=>r.unassigned?<span className="unassigned"><ShieldAlert size={13}/> Chưa phân công</span>:<span>{r.assignees?.map((a:Row)=>a.MaNV).filter((v:string,i:number,a:string[])=>a.indexOf(v)===i).join(', ')}</span>},
 ]}/>;
}
export function Bars({data,color}:{data:{label:string;value:number}[];color?:string}){
 const max=Math.max(1,...data.map(d=>d.value));
 return <div className="w-bars">{data.map(d=><div className="w-bar" key={d.label}><span>{d.label}</span><div><i style={{width:`${d.value/max*100}%`,background:color}}/></div><b>{d.value}</b></div>)}{!data.length&&<div className="w-empty">Chưa có dữ liệu</div>}</div>;
}
export function Timeline({events}:{events:Row[]}){return <ol className="w-timeline">{events.map((e,i)=><li key={i}><span className="timeline-dot"/><div><time>{date(e.time)}</time><b>{e.title}</b><small>{e.employee}{e.minutes?` · ${e.minutes} phút`:''}</small></div></li>)}{!events.length&&<li>Chưa có lịch sử xử lý.</li>}</ol>}
export function Stats({items}:{items:{label:string;value:React.ReactNode;hint?:string}[]}){return <div className="w-stats">{items.map(s=><div className="w-stat" key={s.label}><small>{s.label}</small><strong>{s.value}</strong>{s.hint&&<span>{s.hint}</span>}</div>)}</div>}
