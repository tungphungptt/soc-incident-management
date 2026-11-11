import {useEffect,useState} from 'react';
import {Search,ShieldCheck,Network} from 'lucide-react';
import {api} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {go} from '../../app/routing/navigation';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {Badge} from '../../shared/components/Badge';
import {Stats} from '../../shared/components/Stats';
import {RoleTabs} from '../../shared/components/RoleTabs';
import {CreateIncident} from '../../features/incidents/CreateIncident';
import {CreateIOC} from '../../features/intelligence/CreateIOC';
import {Input,Select} from '../../shared/forms/fields';
import {WorkspaceProps} from '../../app/types';
import {techColumns,iocColumns} from '../../features/reporting/columns';
import './ui4.css';

export function HunterLayout(p:WorkspaceProps){
 const [intel,setIntel]=useState<Row>({iocs:[],techniques:[]}),[error,setError]=useState(''),[tab,setTab]=useState('explorer'),[searched,setSearched]=useState(false);
 const load=async(query='')=>{try{setIntel(await api(p.token,'/workspace/intelligence?'+query));setError('');if(query)setSearched(true)}catch(e:any){setError(e.message)}};
 useEffect(()=>{load()},[p.token]);
 const submit=(event:React.FormEvent<HTMLFormElement>)=>{event.preventDefault();load(new URLSearchParams(new FormData(event.currentTarget) as any).toString())};
 return <div className="hunter-layout ui4-hunter"><header className="ui4-heading"><span>THREAT INTELLIGENCE EXPLORER</span><h2>Tra cứu và liên kết dấu vết</h2><p>Tìm IOC, đối chiếu MITRE và tạo phát hiện bằng các chức năng hệ thống hiện có.</p></header><Stats items={[{label:'IOC trong kết quả',value:intel.iocs.length},{label:'Technique MITRE',value:intel.techniques.length},{label:'IOC phổ biến',value:(p.reports.top_iocs||[]).length},{label:'Technique phổ biến',value:(p.reports.top_techniques||[]).length}]}/><RoleTabs idPrefix="hunter" label="Khu vực threat intelligence" value={tab} onChange={setTab} items={[{id:'explorer',label:'Threat Explorer'},{id:'reports',label:'Báo cáo tình báo'},{id:'create',label:'Tạo mới'}]}/>{error&&<div className="error-box">{error}</div>}<div id="hunter-panel-explorer" role="tabpanel" aria-labelledby="hunter-explorer" hidden={tab!=='explorer'}><section className="hunt-search"><div className="ui4-search-title"><span><Search size={22}/></span><div><h2>Tìm IOC</h2><p>Hỗ trợ IP, domain, URL, hash và email.</p></div></div><form onSubmit={submit}><div className="hunt-query"><input aria-label="Giá trị IOC" name="value" placeholder="Nhập IP, domain, URL, hash hoặc email…"/><button className="primary">Tra cứu</button></div><details className="ui4-advanced"><summary>Bộ lọc nâng cao</summary><div className="hunt-filters"><Select name="kind" label="Loại" required={false} options={['','IP','Domain','URL','Hash','Email'].map(value=>({value,label:value||'Tất cả'}))}/><Input name="source" label="Nguồn" required={false}/><Select name="confidence" label="Tin cậy" required={false} options={['','HIGH','MEDIUM','LOW'].map(value=>({value,label:value||'Tất cả'}))}/><Input name="technique" label="Technique MITRE" required={false}/></div></details></form></section><div className="ui4-intel-results"><Panel title={`IOC · ${intel.iocs.length} kết quả`} action={searched?<span className="ui4-live-result"><ShieldCheck size={16}/>Kết quả tra cứu</span>:undefined}><DataTable rows={intel.iocs} columns={[{key:'GiaTriIOC',label:'Giá trị'},{key:'LoaiIOC',label:'Loại'},{key:'Nguon',label:'Nguồn'},{key:'MucDoTinCay',label:'Tin cậy',render:row=><Badge value={row.MucDoTinCay}/>},{key:'incidents',label:'Incident cùng IOC',render:row=><div className="w-chips">{row.incidents.map((id:string)=><button className="text-link" key={id} onClick={()=>go(p.profile.role,'incidents/'+id)}>{id}</button>)}</div>}]}/></Panel><Panel title="Tra cứu Technique MITRE" action={<Network size={20}/>}><DataTable rows={intel.techniques} columns={[{key:'MaKyThuat',label:'Technique'},{key:'TenKyThuat',label:'Tên kỹ thuật'},{key:'ChienThuat',label:'Chiến thuật'}]}/></Panel></div></div><div id="hunter-panel-reports" role="tabpanel" aria-labelledby="hunter-reports" hidden={tab!=='reports'}><div className="ui4-report-grid"><Panel title="IOC phổ biến"><DataTable rows={p.reports.top_iocs||[]} columns={iocColumns}/></Panel><Panel title="Technique phổ biến"><DataTable rows={p.reports.top_techniques||[]} columns={techColumns}/></Panel></div></div><div id="hunter-panel-create" role="tabpanel" aria-labelledby="hunter-create" hidden={tab!=='create'}><div className="ui4-create-grid"><CreateIOC token={p.token} after={()=>{load();p.reload()}}/><CreateIncident token={p.token} staff={p.staff} after={p.reload}/></div></div></div>;
}
