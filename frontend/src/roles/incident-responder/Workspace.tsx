import {useState} from 'react';
import {Panel} from '../../shared/components/Panel';
import {IncidentTable} from '../../features/incidents/components/IncidentTable';
import {Badge} from '../../shared/components/Badge';
import {Stats} from '../../shared/components/Stats';
import {RoleTabs} from '../../shared/components/RoleTabs';
import {WorkspaceProps} from '../../app/types';
import {CaseCard} from '../../features/incidents/components/CaseCard';
import {Row} from '../../shared/types';
import {date} from '../../shared/format';
import {searchText} from '../../shared/search';
import './ui4.css';

function ResponseCard({incident,role}:{incident:Row;role:string}) {
 const assignees=(incident.assignees||[]).map((item:Row)=>item.MaNV).filter((value:string,index:number,values:string[])=>values.indexOf(value)===index);
 return <article className="ui4-response-card"><div className="ui4-response-meta"><Badge value={incident.MucDoNghiemTrong}/><time>{date(incident.ThoiGianPhatHien)}</time></div><CaseCard incident={incident} role={role}/><div className="ui4-response-owner"><span>Phụ trách</span><strong>{incident.unassigned?'Chưa phân công':assignees.join(', ')||'—'}</strong></div><div className="ui4-progress" aria-label={`Tiến độ ${incident.TrangThai}`}><i className="done"/><i className="done"/><i className={incident.TrangThai==='REMEDIATING'?'done':''}/><i/><span>{incident.TrangThai==='CONTAINED'?'Đã khoanh vùng':'Đang khắc phục'}</span></div></article>;
}

export function ResponderLayout(p:WorkspaceProps){
 const [tab,setTab]=useState('board'),[query,setQuery]=useState(''),[severity,setSeverity]=useState('');
 const contained=p.incidents.filter(i=>i.TrangThai==='CONTAINED'),remediating=p.incidents.filter(i=>i.TrangThai==='REMEDIATING'),closed=p.incidents.filter(i=>i.TrangThai==='CLOSED');
 const filter=(rows:Row[])=>rows.filter(row=>(!severity||row.MucDoNghiemTrong===severity)&&(!query||searchText(row.MaIncident+' '+row.MoTa).includes(searchText(query))));
 const active=[...contained,...remediating];
 return <div className="responder-layout ui4-responder"><header className="ui4-heading"><span>INCIDENT RESPONSE CENTER</span><h2>Điều phối ứng phó sự cố</h2><p>Theo dõi khoanh vùng, khắc phục và lịch sử đóng trong phạm vi được giao.</p></header><Stats items={[{label:'Đang ứng phó',value:active.length},{label:'Đã khoanh vùng',value:contained.length},{label:'Đang khắc phục',value:remediating.length},{label:'Đã đóng',value:closed.length}]}/><RoleTabs idPrefix="responder" label="Khu vực ứng phó" value={tab} onChange={setTab} items={[{id:'board',label:'Bảng ứng phó'},{id:'history',label:'Lịch sử đã đóng'}]}/><div id="responder-panel-board" role="tabpanel" aria-labelledby="responder-board" hidden={tab!=='board'}><div className="ui4-filters"><label>Tìm Incident<input type="search" placeholder="Mã hoặc mô tả sự cố…" value={query} onChange={event=>setQuery(event.target.value)}/></label><label>Mức độ<select aria-label="Mức độ ứng phó" value={severity} onChange={event=>setSeverity(event.target.value)}><option value="">Tất cả mức độ</option>{Array.from(new Set(active.map(row=>String(row.MucDoNghiemTrong)))).map(value=><option key={value}>{value}</option>)}</select></label></div><p className="ui4-result-count">{filter(active).length} / {active.length} Incident đang ứng phó</p><div className="response-board">{[{state:'CONTAINED',label:'Đã khoanh vùng',rows:filter(contained)},{state:'REMEDIATING',label:'Đang khắc phục',rows:filter(remediating)}].map(column=><section className="board-column" key={column.state}><div className="board-title"><div><Badge value={column.state}/><h2>{column.label}</h2></div><b>{column.rows.length}</b></div>{column.rows.map(incident=><ResponseCard key={incident.MaIncident} incident={incident} role={p.profile.role}/>)}{!column.rows.length&&<div className="w-empty">Không có Incident phù hợp trong cột này.</div>}</section>)}</div></div><div id="responder-panel-history" role="tabpanel" aria-labelledby="responder-history" hidden={tab!=='history'}><Panel title="Lịch sử các Incident đã đóng của tôi"><p className="ui4-panel-intro">Hồ sơ CLOSED trong phạm vi dữ liệu hiện tại. Mở mã Incident để xem bằng chứng và lịch sử xử lý.</p><IncidentTable rows={closed} role={p.profile.role}/></Panel></div></div>;
}
