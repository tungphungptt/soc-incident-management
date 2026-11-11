
import {Row,Profile} from '../../shared/types';

import {Panel} from '../../shared/components/Panel';
import {Badge} from '../../shared/components/Badge';

import {ActionForm} from '../../shared/forms/ActionForm';
import {Input,Select} from '../../shared/forms/fields';
import {StaffSelect} from '../employees/StaffSelect';
import {CreateIOC} from '../intelligence/CreateIOC';

import {useIncidentDetail} from './useIncidentDetail';
type ActionsProps={token:string;profile:Profile;staff:Row[];state:ReturnType<typeof useIncidentDetail>;data:Row};
export function IncidentActions({token,profile,staff,state,data}:ActionsProps){
 const {intel,assignmentRole,setAssignmentRole,load,mutate}=state;
 const r=data.incident,role=profile.role,closed=r.TrangThai==='CLOSED',canWork=data.can_work!==false;
 const actionAllowed=['SOC_MANAGER','SOC_L2','SOC_L3','INCIDENT_RESPONDER'].includes(role)&&!['NEW','CLOSED'].includes(r.TrangThai)&&(role!=='INCIDENT_RESPONDER'||['CONTAINED','REMEDIATING'].includes(r.TrangThai));
 const actionNames=role==='INCIDENT_RESPONDER'||role==='SOC_MANAGER'?['Block IP','Disable Account','Isolate Host','Kill Process','Reset Password','Collect Evidence','Scan Malware']:['Collect Evidence','Scan Malware'];
 const escalateRole:Record<string,string>={SOC_L1:'SOC_L2',SOC_L2:'SOC_L3',SOC_L3:'INCIDENT_RESPONDER'};

 return <aside className="detail-actions">{!canWork&&<div className="workspace-note">Hồ sơ liên quan để tham khảo. Bạn chưa được phân công nên không có quyền cập nhật.</div>}
 {['SOC_MANAGER','SOC_L1'].includes(role)&&r.TrangThai==='NEW'&&<Panel title="Phân loại mức độ"><ActionForm label="Lưu mức độ" onSubmit={d=>mutate('triage',{severity:d.get('severity'),expert_id:d.get('expert_id')||null},'PUT')}><Select label="Mức độ" name="severity" options={['LOW','MEDIUM','HIGH','CRITICAL'].map(s=>({value:s,label:s}))}/><Select label="Chuyên gia L2/L3 khi nâng lên Critical" name="expert_id" required={false} options={[{value:'',label:'Giữ nguyên phân công'},...staff.filter(s=>['SOC_L2','SOC_L3'].includes(s.role)).map(s=>({value:s.employee_id,label:s.name+' · '+s.role}))]}/></ActionForm></Panel>}
 {data.next_status&&<Panel title="Chuyển trạng thái"><ActionForm disabled={r.needs_expert||(data.next_status==='CLOSED'&&!data.actions.length)} label={`Chuyển → ${data.next_status}`} onSubmit={()=>mutate('transition',{status:data.next_status})}><p><Badge value={r.TrangThai}/> → <Badge value={data.next_status}/></p>{data.next_status==='CLOSED'&&<p>Chỉ đóng khi đã ghi ít nhất một hành động xử lý.</p>}</ActionForm></Panel>}
 {canWork&&actionAllowed&&<Panel title="Ghi hành động xử lý"><ActionForm label="Ghi nhật ký" onSubmit={d=>mutate('actions',{action:d.get('action'),result:d.get('result'),minutes:Number(d.get('minutes'))})}><Select name="action" label="Hành động" options={actionNames.map(a=>({value:a,label:a}))}/><Input name="result" label="Kết quả"/><Input name="minutes" label="Thời lượng (phút)" type="number" min={1}/></ActionForm></Panel>}
 {role==='INCIDENT_RESPONDER'&&<Panel title="Checklist ứng phó"><ul className="response-checklist">{actionNames.map(a=><li key={a}><span>{data.actions.some((x:Row)=>x.HanhDong===a)?'✓':'○'}</span>{a}</li>)}</ul><small>Trạng thái checklist lấy từ các hành động đã ghi.</small></Panel>}
 {role==='SOC_MANAGER'&&!closed&&<Panel title="Phân công"><ActionForm label="Phân công nhân viên" onSubmit={d=>mutate('assign',{employee_id:d.get('employee_id'),role:assignmentRole})}><label className="w-field"><span>Vai trò trong Incident</span><select name="assignment_role" value={assignmentRole} onChange={e=>setAssignmentRole(e.target.value)}>{['SOC_MANAGER','SOC_L1','SOC_L2','SOC_L3','INCIDENT_RESPONDER','THREAT_HUNTER'].map(r=><option key={r}>{r}</option>)}</select></label><StaffSelect staff={staff.filter(s=>!data.participants.some((a:Row)=>a.MaNV===s.employee_id&&a.VaiTro===s.role))} filter={[assignmentRole]}/></ActionForm></Panel>}
 {canWork&&escalateRole[role]&&!closed&&<Panel title={`Chuyển cấp → ${escalateRole[role]}`}><ActionForm disabled={(role==='SOC_L3'?r.TrangThai!=='CONTAINED':r.TrangThai!=='INVESTIGATING')} label="Chuyển cấp" onSubmit={d=>mutate('escalate',{employee_id:d.get('employee_id'),role:escalateRole[role]})}><StaffSelect staff={staff} filter={[escalateRole[role]]}/></ActionForm></Panel>}
 {['SOC_MANAGER','SOC_L3'].includes(role)&&!closed&&<Panel title="Phân tích chuyên sâu"><ActionForm label="Lưu phân tích" onSubmit={d=>mutate('analysis',{description:d.get('description'),risk_score:Number(d.get('risk_score'))},'PUT')}><Input label="Mô tả phân tích" name="description" defaultValue={r.MoTa}/><Input label="Risk Score (0–100)" name="risk_score" type="number" min={0} max={100} defaultValue={r.DiemRuiRo}/></ActionForm></Panel>}
 {canWork&&['SOC_MANAGER','SOC_L2','SOC_L3','THREAT_HUNTER'].includes(role)&&!closed&&<><Panel title="Gắn IOC"><ActionForm label="Gắn IOC" onSubmit={d=>(()=>{const [ioc_type,value]=JSON.parse(String(d.get('value')));return mutate('links',{kind:'ioc',value,ioc_type})})()}><Select name="value" label="IOC có sẵn" options={intel.iocs.map((a:Row)=>({value:JSON.stringify([a.LoaiIOC,a.GiaTriIOC]),label:a.LoaiIOC+' | '+a.GiaTriIOC}))}/></ActionForm></Panel><Panel title="Gắn Technique"><ActionForm label="Gắn Technique" onSubmit={d=>mutate('links',{kind:'technique',value:d.get('value')})}><Select name="value" label="Technique" options={intel.techniques.map((a:Row)=>({value:a.MaKyThuat,label:a.MaKyThuat+' · '+a.TenKyThuat}))}/></ActionForm></Panel><CreateIOC token={token} after={load}/></>}
 </aside>;
}
