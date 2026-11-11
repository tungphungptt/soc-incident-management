import {Row} from '../../shared/types';
import {Select} from '../../shared/forms/fields';

export function StaffSelect({staff,name='employee_id',filter}:{staff:Row[];name?:string;filter?:string[]}){
 return <Select label="Nhân viên" name={name} options={[{value:'',label:'Chọn nhân viên'},...staff.filter(s=>!filter||filter.includes(s.role)).map(s=>({value:s.employee_id,label:`${s.name} · ${s.role}`}))]}/>;
}
