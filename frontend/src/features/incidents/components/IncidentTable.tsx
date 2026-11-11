import {ArrowUpRight,ShieldAlert} from 'lucide-react';
import {Row} from '../../../shared/types';
import {go} from '../../../app/routing/navigation';
import {Badge} from '../../../shared/components/Badge';
import {DataTable} from '../../../shared/components/DataTable';
import {SLABadge} from './SLABadge';

export function IncidentTable({rows,role}:{rows:Row[];role:string}){
 return <DataTable rows={rows} columns={[
 {key:'MaIncident',label:'Incident',render:r=><button className="text-link" onClick={()=>go(role,'incidents/'+r.MaIncident)}>{r.MaIncident}<ArrowUpRight size={13}/></button>},
 {key:'MucDoNghiemTrong',label:'Mức độ',render:r=><Badge value={r.MucDoNghiemTrong}/>},
 {key:'TrangThai',label:'Trạng thái',render:r=><Badge value={r.TrangThai}/>},
 {key:'sla',label:'Đồng hồ SLA',render:r=><SLABadge incident={r}/>},
 {key:'assignees',label:'Phụ trách',render:r=>r.unassigned?<span className="unassigned"><ShieldAlert size={13}/> Chưa phân công</span>:<span>{r.assignees?.map((a:Row)=>a.MaNV).filter((v:string,i:number,a:string[])=>a.indexOf(v)===i).join(', ')}</span>},
 ]}/>;
}
