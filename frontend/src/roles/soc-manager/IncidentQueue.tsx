import {useState} from 'react';
import {Row} from '../../shared/types';
import {searchText} from '../../shared/search';
import {IncidentTable} from '../../features/incidents/components/IncidentTable';

export function IncidentQueue({rows,role}:{rows:Row[];role:string}){
 const [query,setQuery]=useState(''),[status,setStatus]=useState(''),[severity,setSeverity]=useState('');
 const options=(key:string)=>Array.from(new Set(rows.map(row=>String(row[key])))).sort();
 const filtered=rows.filter(row=>(!status||row.TrangThai===status)&&(!severity||row.MucDoNghiemTrong===severity)&&(!query||searchText(row.MaIncident+' '+row.MoTa).includes(searchText(query))));
 return <><div className="ui2-filters"><label>Tìm Incident<input type="search" placeholder="Mã hoặc mô tả Incident…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Trạng thái<select aria-label="Trạng thái" value={status} onChange={e=>setStatus(e.target.value)}><option value="">Tất cả trạng thái</option>{options('TrangThai').map(value=><option key={value}>{value}</option>)}</select></label><label>Mức độ<select aria-label="Mức độ" value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">Tất cả mức độ</option>{options('MucDoNghiemTrong').map(value=><option key={value}>{value}</option>)}</select></label></div><p className="ui2-result-count">{filtered.length} / {rows.length} Incident đã tải</p><IncidentTable rows={filtered} role={role}/></>;
}
