import {RoleTabs} from '../../shared/components/RoleTabs';
import {AnalystQueue} from '../../features/analysis/AnalystQueue';
import {searchText} from '../../shared/search';
import {useEffect,useState} from 'react';
import {api,allRows} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {IncidentTable} from '../../features/incidents/components/IncidentTable';
import {Badge} from '../../shared/components/Badge';
import {CreateIncident} from '../../features/incidents/CreateIncident';
import {WorkspaceProps} from '../../app/types';
import {assetColumns} from '../../features/reporting/columns';

export function AnalystL1Layout(p:WorkspaceProps){
 const [alerts,setAlerts]=useState<Row[]>([]),[selected,setSelected]=useState<string[]>([]),[severity,setSeverity]=useState(''),[error,setError]=useState('');
 const [tab,setTab]=useState('triage'),[alertQuery,setAlertQuery]=useState('');
 const [from,setFrom]=useState(''),[to,setTo]=useState(''),[lookup,setLookup]=useState<Row[]>([]);
 useEffect(()=>{allRows(p.token,'canh_bao').then(setAlerts).catch(e=>setError(e.message))},[p.token,p.incidents]);
 const fresh=p.incidents.filter(i=>i.TrangThai==='NEW'&&(!severity||i.MucDoNghiemTrong===severity));
 const newKeys=new Set(p.incidents.filter(i=>i.TrangThai==='NEW').map(i=>i.MaIncident));
 return <div className="l1-layout ui3-l1"><header className="ui3-heading"><span>TIẾP NHẬN & PHÂN LOẠI</span><h2>Hàng đợi giám sát</h2><p>Ưu tiên sự cố mới, gom cảnh báo liên quan và chuyển đúng người xử lý.</p></header><RoleTabs idPrefix="l1" label="Khu vực phân loại" value={tab} onChange={setTab} items={[{id:'triage',label:'Tiếp nhận & phân loại'},{id:'lookup',label:'Tra cứu theo ngày'},{id:'assets',label:'Tài sản nổi bật'}]}/>{error&&<div className="error-box">{error}</div>}<div className="ui3-triage-grid" id="l1-panel-triage" role="tabpanel" aria-labelledby="l1-triage" hidden={tab!=='triage'}><div className="queue-main"><div className="queue-banner"><div><strong>{fresh.length}</strong><span>Incident NEW cần phân loại</span></div><div><strong>{fresh.filter(i=>i.unassigned).length}</strong><span>Chưa có phụ trách</span></div><label>Mức độ<select value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">Tất cả mức độ</option>{['CRITICAL','HIGH','MEDIUM','LOW'].map(s=><option key={s}>{s}</option>)}</select></label></div>
 <Panel title="Hàng đợi Incident · Critical trước"><AnalystQueue rows={fresh} role={p.profile.role} filterSeverity={false}/></Panel>
 <Panel title="Cảnh báo mới · chọn để gom Incident"><div className="ui3-alert-toolbar"><label>Tìm cảnh báo<input type="search" placeholder="Mã, nội dung hoặc Incident nguồn…" value={alertQuery} onChange={e=>setAlertQuery(e.target.value)}/></label><span>{selected.length} cảnh báo đã chọn</span></div><DataTable rows={alerts.filter(a=>newKeys.has(a.MaIncident)&&(!severity||a.MucDoNghiemTrong===severity)&&(!alertQuery||searchText(a.MaCanhBao+' '+a.NoiDung+' '+a.MaIncident).includes(searchText(alertQuery)))).sort((a,b)=>['CRITICAL','HIGH','MEDIUM','LOW'].indexOf(a.MucDoNghiemTrong)-['CRITICAL','HIGH','MEDIUM','LOW'].indexOf(b.MucDoNghiemTrong))} columns={[{key:'select',label:'Chọn',render:r=><input type="checkbox" aria-label={'Chọn '+r.MaCanhBao} checked={selected.includes(r.MaCanhBao)} onChange={e=>setSelected(s=>e.target.checked?[...s,r.MaCanhBao]:s.filter(k=>k!==r.MaCanhBao))}/>},{key:'MaCanhBao',label:'Cảnh báo'},{key:'NoiDung',label:'Nội dung'},{key:'MucDoNghiemTrong',label:'Mức độ',render:r=><Badge value={r.MucDoNghiemTrong}/>},{key:'MaIncident',label:'Incident nguồn'}]}/></Panel>
</div>
 <aside className="ui3-create"><div className="ui3-process"><b>Quy trình tiếp nhận</b><ol><li>Chọn cảnh báo liên quan nếu cần gom.</li><li>Mô tả phát hiện và chọn mức độ.</li><li>Critical cần chuyên gia L2/L3.</li></ol></div><CreateIncident token={p.token} staff={p.staff} alertIds={selected} after={()=>{setSelected([]);p.reload()}}/><div className="workspace-note">SLA: Critical 1 giờ · High 4 giờ · Medium 12 giờ · Low 24 giờ.</div></aside></div><div id="l1-panel-lookup" role="tabpanel" aria-labelledby="l1-lookup" hidden={tab!=='lookup'}> <Panel title="Tra cứu Incident theo khoảng ngày"><form className="w-inline" onSubmit={async e=>{e.preventDefault();try{setLookup(await api(p.token,`/workspace/incidents?date_from=${from}&date_to=${to}`));setError('')}catch(e:any){setError(e.message)}}}><label>Từ ngày<input type="date" required value={from} onChange={e=>setFrom(e.target.value)}/></label><label>Đến ngày<input type="date" required value={to} onChange={e=>setTo(e.target.value)}/></label><button className="secondary">Tra cứu</button></form><IncidentTable rows={lookup} role={p.profile.role}/></Panel></div><div id="l1-panel-assets" role="tabpanel" aria-labelledby="l1-assets" hidden={tab!=='assets'}><Panel title={`Top 10 tài sản · ${p.month}`}><DataTable rows={p.reports.top_assets||[]} columns={assetColumns}/></Panel></div></div>;
}
