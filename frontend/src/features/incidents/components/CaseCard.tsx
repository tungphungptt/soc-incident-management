import {Row} from '../../../shared/types';
import {go} from '../../../app/routing/navigation';
import {Badge} from '../../../shared/components/Badge';
import {SLABadge} from './SLABadge';

export function CaseCard({incident:r,role}:{incident:Row;role:string}){
 return <button className={`case-card case-${r.MucDoNghiemTrong.toLowerCase()}`} onClick={()=>go(role,'incidents/'+r.MaIncident)}><div className="case-card-top"><b>{r.MaIncident}</b><Badge value={r.MucDoNghiemTrong}/></div><p>{r.MoTa}</p><SLABadge incident={r}/>{r.needs_expert&&<small className="unassigned">Cần L2/L3 tham gia</small>}<span className="case-open">Mở hồ sơ →</span></button>;
}
