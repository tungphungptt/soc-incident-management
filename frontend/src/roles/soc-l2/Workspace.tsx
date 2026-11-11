import {useState} from 'react';
import {RoleTabs} from '../../shared/components/RoleTabs';
import {Stats} from '../../shared/components/Stats';
import {Badge} from '../../shared/components/Badge';
import {date} from '../../shared/format';
import {searchText} from '../../shared/search';
import '../../features/analysis/analyst.css';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {WorkspaceProps} from '../../app/types';
import {assetColumns} from '../../features/reporting/columns';
import {CaseCard} from '../../features/incidents/components/CaseCard';
import {SharedIOC} from '../../features/intelligence/SharedIOC';

export function AnalystL2Layout(p:WorkspaceProps){
 const [tab,setTab]=useState('cases'),[query,setQuery]=useState(''),[severity,setSeverity]=useState('');
 const cases=p.incidents.filter(i=>i.TrangThai==='INVESTIGATING');
 const visible=cases.filter(c=>(!severity||c.MucDoNghiemTrong===severity)&&(!query||searchText(c.MaIncident+' '+c.MoTa).includes(searchText(query))));
 return <div className="l2-layout ui3-l2"><header className="ui3-heading"><span>INVESTIGATION WORKSPACE</span><h2>Không gian điều tra</h2><p>Hồ sơ được giao, bằng chứng và tương quan kỹ thuật trong phạm vi của bạn.</p></header><Stats items={[{label:'Đang điều tra',value:cases.length},{label:'Critical / High',value:cases.filter(c=>['CRITICAL','HIGH'].includes(c.MucDoNghiemTrong)).length},{label:'Cần chuyên gia',value:cases.filter(c=>c.needs_expert).length}]}/><RoleTabs idPrefix="l2" label="Khu vực điều tra" value={tab} onChange={setTab} items={[{id:'cases',label:'Hồ sơ được giao'},{id:'correlation',label:'Tương quan IOC'},{id:'assets',label:'Tài sản liên quan'}]}/><div className="ui3-investigation-grid" id="l2-panel-cases" role="tabpanel" aria-labelledby="l2-cases" hidden={tab!=='cases'}><aside className="investigation-rail"><span className="workspace-kicker">INVESTIGATION DESK</span><h2>Quy trình điều tra</h2><p>Incident INVESTIGATING được phân công hoặc chuyển từ L1.</p><ol><li>Thu thập bằng chứng</li><li>Phân tích IOC / MITRE</li><li>Scan Malware</li><li>Khoanh vùng hoặc chuyển L3</li></ol></aside><div><Panel title="Bàn điều tra · Sự cố được giao"><div className="ui3-filters"><label>Tìm hồ sơ<input type="search" placeholder="Mã hoặc mô tả điều tra…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label>Mức độ<select aria-label="Mức độ hồ sơ" value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">Tất cả mức độ</option>{Array.from(new Set(cases.map(c=>String(c.MucDoNghiemTrong)))).map(value=><option key={value}>{value}</option>)}</select></label></div><p className="ui3-result-count">{visible.length} / {cases.length} hồ sơ đã tải</p><div className="case-grid">{visible.map(c=><article className="ui3-case" key={c.MaIncident}><div className="ui3-case-meta"><Badge value={c.TrangThai}/><time>{date(c.ThoiGianPhatHien)}</time></div><CaseCard incident={c} role={p.profile.role}/></article>)}{!visible.length&&<div className="w-empty">Không có hồ sơ INVESTIGATING phù hợp.</div>}</div></Panel></div></div><div id="l2-panel-assets" role="tabpanel" aria-labelledby="l2-assets" hidden={tab!=='assets'}><Panel title="Tài sản phát sinh nhiều cảnh báo"><DataTable rows={p.reports.top_assets||[]} columns={assetColumns}/></Panel></div><div id="l2-panel-correlation" role="tabpanel" aria-labelledby="l2-correlation" hidden={tab!=='correlation'}><Panel title="Tương quan Incident cùng IOC"><SharedIOC rows={p.reports.same_ioc||[]} role={p.profile.role}/></Panel></div></div>;
}
