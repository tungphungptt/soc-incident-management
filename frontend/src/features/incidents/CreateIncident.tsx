import {post} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {Panel} from '../../shared/components/Panel';
import {ActionForm} from '../../shared/forms/ActionForm';
import {Input,Select} from '../../shared/forms/fields';

export function CreateIncident({token,staff,alertIds=[],after}:{token:string;staff:Row[];alertIds?:string[];after:()=>void}){
 return <Panel title={alertIds.length?`Gom ${alertIds.length} cảnh báo`:'Tạo Incident từ phát hiện'}><ActionForm label="Tạo sự cố NEW" onSubmit={async d=>{if(d.get('severity')==='CRITICAL'&&!d.get('expert_id'))throw new Error('Incident Critical bắt buộc chọn chuyên gia L2/L3.');const r=await post(token,'/workspace/incidents',{description:d.get('description'),severity:d.get('severity'),expert_id:d.get('expert_id')||null,alert_ids:alertIds});after();return r;}}>
 <Input label="Mô tả phát hiện" name="description"/><Select label="Mức độ nghiêm trọng" name="severity" options={['LOW','MEDIUM','HIGH','CRITICAL'].map(s=>({value:s,label:s}))}/>
 <Select label="Chuyên gia L2/L3 (bắt buộc với Critical)" name="expert_id" required={false} options={[{value:'',label:'Chưa chọn'},...staff.filter(s=>['SOC_L2','SOC_L3'].includes(s.role)).map(s=>({value:s.employee_id,label:s.name+' · '+s.role}))]}/>
 </ActionForm></Panel>;
}
