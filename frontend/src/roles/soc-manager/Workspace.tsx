import './ui2.css';
import {IncidentQueue} from './IncidentQueue';
import {Button} from '../../shared/components/Button';
import {useState} from 'react';
import {RoleTabs} from '../../shared/components/RoleTabs';
import {post} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {money} from '../../shared/format';
import {Panel} from '../../shared/components/Panel';
import {DataTable} from '../../shared/components/DataTable';
import {IncidentTable} from '../../features/incidents/components/IncidentTable';
import {Badge} from '../../shared/components/Badge';
import {Stats} from '../../shared/components/Stats';
import {Bars} from '../../shared/components/Bars';
import {ActionForm} from '../../shared/forms/ActionForm';
import {Input} from '../../shared/forms/fields';
import {StaffSelect} from '../../features/employees/StaffSelect';
import {WorkspaceProps} from '../../app/types';

export function ManagerLayout(p:WorkspaceProps){
 const r=p.reports;
 const [tab,setTab]=useState('overview');
 const employeeColumns=[{key:'HoTen',label:'Nhân viên'},{key:'active_count',label:'Đang xử lý'},{key:'overloaded',label:'Tải',render:(r:Row)=>r.overloaded?<Badge value="HIGH"/>:'Bình thường'},
 {key:'participated_count',label:'Tham gia trong tháng'},{key:'closed_count',label:'Đóng trong tháng'},{key:'average_minutes',label:'TB xử lý (phút)'},{key:'bonus',label:'Thưởng',render:(r:Row)=>money(r.bonus)},{key:'base_salary',label:'Lương',render:(r:Row)=>money(r.base_salary)},{key:'total',label:'Lương + thưởng',render:(r:Row)=>money(r.total)}];
 return <div className="manager-layout ui2-manager"><div className="ui2-heading"><span>ĐIỀU HÀNH SOC · {p.month}</span><h2>Hiệu quả vận hành & mức độ rủi ro</h2><p>Theo dõi tình hình, ưu tiên xử lý và phân bổ nguồn lực.</p></div><RoleTabs idPrefix="manager" label="Khu vực điều hành" value={tab} onChange={setTab} items={[{id:'overview',label:'Tổng quan'},{id:'incidents',label:'Điều phối Incident'},{id:'risk',label:'Rủi ro tổ chức'},{id:'people',label:'Hiệu suất nhân viên'},{id:'pay',label:'Lương & thưởng'}]}/><div id="manager-panel-overview" role="tabpanel" aria-labelledby="manager-overview" hidden={tab!=='overview'}><Stats items={[{label:'Incident',value:p.incidents.length},{label:'Vi phạm SLA',value:r.sla_violated??0,hint:'Gồm vi phạm trước khi đóng'},{label:'Chưa có phụ trách',value:r.unassigned_count??0},{label:'Nhân viên quá tải',value:r.employees?.filter((e:Row)=>e.overloaded).length??0,hint:`Ngưỡng ${r.overload_threshold??'—'} Incident đang xử lý`}]}/>
 <div className="w-columns"><Panel title="Theo trạng thái"><Bars data={Object.entries(r.by_status||{}).map(([label,value])=>({label,value:Number(value)}))}/></Panel><Panel title="Theo mức độ"><Bars data={Object.entries(r.by_severity||{}).map(([label,value])=>({label,value:Number(value)}))}/></Panel></div>
 <div className="ui2-command-grid"><Panel title="Ưu tiên rủi ro"><p className="ui2-command-value">{r.top_organizations?.[0]?.risk_score??'—'} <span>Risk Score</span></p><p>{r.top_organizations?.[0]?.TenTC||'Chưa có dữ liệu tổ chức'}</p><Button variant="secondary" onClick={()=>setTab('risk')}>Xem rủi ro tổ chức</Button></Panel><Panel title="Điều phối & nguồn lực"><p className="ui2-section-note">Theo dõi Incident, hiệu suất và thu nhập theo kỳ báo cáo đang chọn.</p><div className="ui2-command-actions"><Button variant="secondary" onClick={()=>setTab('incidents')}>Điều phối Incident</Button><Button variant="secondary" onClick={()=>setTab('people')}>Hiệu suất nhân viên</Button><Button variant="secondary" onClick={()=>setTab('pay')}>Lương & thưởng</Button></div></Panel></div></div><div id="manager-panel-risk" role="tabpanel" aria-labelledby="manager-risk" hidden={tab!=='risk'}><div className="manager-risk-grid"><Panel title="Risk Score · Top 10 tổ chức"><DataTable rows={r.top_organizations||[]} columns={[{key:'TenTC',label:'Tổ chức'},{key:'risk_score',label:'Risk Score'},{key:'critical',label:'Critical'},{key:'high',label:'High'}]}/><small>Critical ×10 + High ×5 + Medium ×2 + Low. Mỗi Incident tính một lần/tổ chức.</small></Panel><Panel title="Tổ chức nhiều Critical + High"><Bars data={(r.critical_high_organizations||[]).map((o:Row)=>({label:o.TenTC,value:o.critical+o.high}))}/></Panel></div>
 <Panel title="Risk Score · Toàn bộ tổ chức"><DataTable rows={r.organizations||[]} columns={[{key:'TenTC',label:'Tổ chức'},{key:'risk_score',label:'Risk Score'},{key:'critical',label:'Critical'},{key:'high',label:'High'}]}/></Panel></div><div id="manager-panel-incidents" role="tabpanel" aria-labelledby="manager-incidents" hidden={tab!=='incidents'}><p className="ui2-section-note">Ưu tiên các hồ sơ vi phạm SLA. Mở mã Incident để phân công và xử lý theo quyền hiện có.</p><Panel title="Đang xử lý · Đã vi phạm SLA"><IncidentTable rows={r.overdue||[]} role={p.profile.role}/></Panel>
<Panel title="Toàn bộ sự cố"><IncidentQueue rows={p.incidents} role={p.profile.role}/></Panel></div><div id="manager-panel-people" role="tabpanel" aria-labelledby="manager-people" hidden={tab!=='people'}><Panel title={`Hiệu suất nhân viên · ${p.month}`}><DataTable rows={r.employees||[]} columns={employeeColumns.slice(0,6)}/></Panel>
 <Panel title="Incident tham gia theo tháng phát hiện"><DataTable rows={(r.employees||[]).flatMap((e:Row)=>(e.participation_monthly||[]).map((m:Row)=>({name:e.HoTen,...m})))} columns={[{key:'name',label:'Nhân viên'},{key:'month',label:'Tháng phát hiện'},{key:'count',label:'Incident tham gia'}]}/></Panel>
 </div><div id="manager-panel-pay" role="tabpanel" aria-labelledby="manager-pay" hidden={tab!=='pay'}><p className="ui2-section-note">Kỳ lương {p.month}. Các chỉ số thu nhập và thưởng được cung cấp bởi hệ thống.</p><Panel title={`Thu nhập nhân viên · ${p.month}`}><DataTable rows={r.employees||[]} columns={[employeeColumns[0],...employeeColumns.slice(6)]}/></Panel><div className="w-columns"><Panel title="Lương cơ bản theo tháng"><ActionForm onSubmit={async d=>{const result=await post(p.token,'/workspace/compensation',{employee_id:d.get('employee_id'),month:p.month,base_salary:Number(d.get('base_salary'))},'PUT');p.reload();return result;}}><StaffSelect staff={p.staff}/><Input name="base_salary" label="Lương cơ bản (VND)" type="number" min={0}/></ActionForm></Panel><Panel title="Incident đã đóng theo tháng · từng nhân viên"><DataTable rows={(r.employees||[]).flatMap((e:Row)=>(e.monthly||[]).map((m:Row)=>({name:e.HoTen,...m})))} columns={[{key:'name',label:'Nhân viên'},{key:'month',label:'Tháng'},{key:'count',label:'Đã đóng'}]}/></Panel></div>
 </div></div>;
}
