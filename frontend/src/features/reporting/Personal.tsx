import {useEffect,useState} from 'react';
import {api} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {money} from '../../shared/format';
import {Panel} from '../../shared/components/Panel';
import {Stats} from '../../shared/components/Stats';
import {Bars} from '../../shared/components/Bars';

export function Personal({token,month}:{token:string;month:string}){
 const [data,setData]=useState<Row|null>(null),[error,setError]=useState('');
 useEffect(()=>{setData(null);api(token,'/workspace/personal?month='+month).then(setData).catch(e=>setError(e.message))},[token,month]);
 return <div className="personal-layout">{error&&<div className="error-box">{error}</div>}{data&&<><Stats items={[{label:'Incident đã đóng · '+month,value:data.closed_count},{label:'Thưởng tháng',value:money(data.bonus)},{label:'Lương cơ bản',value:money(data.base_salary)},{label:'Lương + thưởng',value:money(data.total)}]}/><Panel title="Incident đã xử lý theo tháng"><Bars data={data.monthly.map((r:Row)=>({label:r.month,value:r.count}))}/><p>{data.note}</p><small>Dữ liệu của chính tài khoản đăng nhập · Mã nhân viên {data.employee_id}</small></Panel></>}</div>;
}
