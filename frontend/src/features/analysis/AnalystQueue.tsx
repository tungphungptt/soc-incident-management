import {useState} from 'react';
import {Row} from '../../shared/types';
import {searchText} from '../../shared/search';
import {date} from '../../shared/format';
import {IncidentTable} from '../incidents/components/IncidentTable';
import './analyst.css';

/** Filters only the records already authorized and returned by the backend. */
export function AnalystQueue({rows,role,filterSeverity=true}:{rows:Row[];role:string;filterSeverity?:boolean}) {
 const [query,setQuery]=useState(''),[severity,setSeverity]=useState('');
 const filtered=rows.filter(row=>(!severity||row.MucDoNghiemTrong===severity)&&(!query||searchText(row.MaIncident+' '+row.MoTa).includes(searchText(query))));
 return <div className="ui3-queue"><div className="ui3-filters"><label>Tìm Incident<input type="search" placeholder="Mã hoặc mô tả sự cố…" value={query} onChange={e=>setQuery(e.target.value)}/></label>{filterSeverity&&<label>Mức độ trong hàng đợi<select aria-label="Mức độ trong hàng đợi" value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">Tất cả mức độ</option>{Array.from(new Set(rows.map(row=>String(row.MucDoNghiemTrong)))).map(value=><option key={value}>{value}</option>)}</select></label>}</div><p className="ui3-result-count">{filtered.length} / {rows.length} Incident đã tải · Giữ thứ tự ưu tiên của hàng đợi</p>{filtered[0]&&<div className="ui3-queue-clock"><span>Đầu hàng đợi <strong>{filtered[0].MaIncident}</strong></span><span>Phát hiện <time>{date(filtered[0].ThoiGianPhatHien)}</time></span></div>}<IncidentTable rows={filtered} role={role}/></div>;
}
