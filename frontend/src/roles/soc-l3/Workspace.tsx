import {useState} from 'react';
import {RoleTabs} from '../../shared/components/RoleTabs';
import {Stats} from '../../shared/components/Stats';
import {AnalystQueue} from '../../features/analysis/AnalystQueue';
import {Row} from '../../shared/types';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {Bars} from '../../shared/components/Bars';
import {WorkspaceProps} from '../../app/types';
import {assetColumns,iocColumns} from '../../features/reporting/columns';
import {SharedIOC} from '../../features/intelligence/SharedIOC';

export function AnalystL3Layout(p:WorkspaceProps){
 const [tab,setTab]=useState('priority');
 const cases=p.incidents.filter(i=>['CRITICAL','HIGH'].includes(i.MucDoNghiemTrong)&&i.TrangThai!=='CLOSED').sort((a,b)=>Number(b.needs_expert)-Number(a.needs_expert));
 return <div className="l3-layout ui3-l3"><div className="analysis-hero"><div><span className="workspace-kicker">ADVANCED ANALYTICS</span><h2>Ưu tiên rủi ro cao</h2><p>Phân tích kỹ thuật, tương quan và các tài sản cần điều tra sâu.</p></div><strong>{cases.length}<small>Critical / High đang mở</small></strong></div><Stats items={[{label:'Critical đang mở',value:cases.filter(c=>c.MucDoNghiemTrong==='CRITICAL').length},{label:'High đang mở',value:cases.filter(c=>c.MucDoNghiemTrong==='HIGH').length},{label:'Cần chuyên gia L2/L3',value:cases.filter(c=>c.needs_expert).length}]}/><RoleTabs idPrefix="l3" label="Khu vực phân tích" value={tab} onChange={setTab} items={[{id:'priority',label:'Sự cố ưu tiên'},{id:'intelligence',label:'MITRE & IOC'},{id:'assets',label:'Tài sản cần chú ý'}]}/><div id="l3-panel-priority" role="tabpanel" aria-labelledby="l3-priority" hidden={tab!=='priority'}><Panel title="Critical / High · Ưu tiên cần L2/L3"><AnalystQueue rows={cases} role={p.profile.role}/></Panel></div><div id="l3-panel-intelligence" role="tabpanel" aria-labelledby="l3-intelligence" hidden={tab!=='intelligence'}><div className="analysis-grid"><Panel title="Technique MITRE phổ biến nhất"><Bars data={(p.reports.top_techniques||[]).map((r:Row)=>({label:r.MaKyThuat,value:r.incident_count}))}/></Panel><Panel className="ui3-ioc-panel" title="IOC xuất hiện nhiều Incident"><DataTable rows={p.reports.top_iocs||[]} columns={iocColumns}/></Panel><Panel title="Incident có cùng IOC"><SharedIOC rows={p.reports.same_ioc||[]} role={p.profile.role}/></Panel></div></div><div id="l3-panel-assets" role="tabpanel" aria-labelledby="l3-assets" hidden={tab!=='assets'}><Panel title="Nhiều cảnh báo · Chưa có Incident CLOSED"><DataTable rows={p.reports.never_closed_assets||[]} columns={assetColumns}/></Panel></div></div>;
}
