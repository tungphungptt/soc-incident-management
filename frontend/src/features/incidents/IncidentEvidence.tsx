
import {Row} from '../../shared/types';
import {date} from '../../shared/format';
import {go} from '../../app/routing/navigation';
import {Panel} from '../../shared/components/Panel';

import {DataTable} from '../../shared/components/DataTable';
import {Timeline} from './components/Timeline';
import {Stats} from '../../shared/components/Stats';

export function IncidentEvidence({data,role}:{data:Row;role:string}){
 const r=data.incident;
 return <div className="detail-evidence"><Panel title="Hồ sơ sự cố"><p>{r.MoTa}</p><Stats items={[{label:'Risk Score',value:r.DiemRuiRo},{label:'Phát hiện',value:date(r.ThoiGianPhatHien)},{label:'Hành động đã ghi',value:data.actions.length}]}/></Panel>
 <Panel title="Cảnh báo liên quan"><DataTable rows={data.alerts} columns={[{key:'MaCanhBao',label:'Cảnh báo'},{key:'NoiDung',label:'Nội dung'},{key:'IPNguon',label:'IP nguồn'},{key:'IPDich',label:'IP đích'}]}/></Panel>
 <div className="w-columns"><Panel title="Tài sản"><DataTable rows={data.assets} columns={[{key:'Ten',label:'Tài sản'},{key:'DiaChiIP',label:'IP'},{key:'MaTC',label:'Tổ chức'}]}/></Panel><Panel title="IOC liên quan"><DataTable rows={data.iocs} columns={[{key:'LoaiIOC',label:'Loại'},{key:'GiaTriIOC',label:'Giá trị'},{key:'MucDoTinCay',label:'Tin cậy'}]}/></Panel></div>
 <Panel title="Technique MITRE"><DataTable rows={data.techniques} columns={[{key:'MaKyThuat',label:'ID'},{key:'TenKyThuat',label:'Kỹ thuật'},{key:'ChienThuat',label:'Chiến thuật'}]}/></Panel>
 <Panel title="Nhân viên tham gia"><DataTable rows={data.participants} columns={[{key:'name',label:'Nhân viên'},{key:'VaiTro',label:'Vai trò'},{key:'ThoiDiemThamGia',label:'Tham gia',render:a=>date(a.ThoiDiemThamGia)}]}/></Panel>
 <Panel title="Incident cùng IOC"><div className="w-chips">{data.same_ioc_incidents.map((key:string)=><button className="secondary" key={key} onClick={()=>go(role,'incidents/'+key)}>{key}</button>)}{!data.same_ioc_incidents.length&&<p>Chưa có Incident cùng IOC.</p>}</div></Panel>
 <Panel title="Lịch sử xử lý đầy đủ"><Timeline events={data.timeline}/></Panel></div>;
}
