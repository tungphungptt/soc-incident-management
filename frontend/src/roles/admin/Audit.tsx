import {useState} from 'react';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {Row} from '../../shared/types';
import {date} from '../../shared/format';
import {searchText} from '../../shared/search';

export function AdminAudit({rows}:{rows:Row[]}){
 const [query,setQuery]=useState(''),[action,setAction]=useState('');
 const filtered=rows.filter(row=>(!action||row.action===action)&&(!query||searchText(Object.values(row).join(' ')).includes(searchText(query))));
 return <div className="ui2-admin"><Panel title="Nhật ký hoạt động"><p>Tra cứu các bản ghi được hệ thống trả về. Bộ lọc áp dụng trên dữ liệu đã tải.</p><div className="ui2-filters"><label>Tìm nhật ký<input type="search" placeholder="Người thực hiện, đối tượng, chi tiết…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Hành động<select aria-label="Hành động" value={action} onChange={e=>setAction(e.target.value)}><option value="">Tất cả hành động</option>{Array.from(new Set(rows.map(row=>String(row.action)))).sort().map(value=><option key={value}>{value}</option>)}</select></label></div><p className="ui2-result-count">{filtered.length} / {rows.length} bản ghi đã tải</p><DataTable rows={filtered} columns={[{key:'created_at',label:'Thời điểm',render:r=>date(r.created_at)},{key:'username',label:'Người thực hiện'},{key:'action',label:'Hành động'},{key:'target',label:'Đối tượng'},{key:'detail',label:'Chi tiết'}]}/></Panel></div>;
}
