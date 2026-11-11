
import {Row,Profile} from '../../shared/types';
import {go} from '../../app/routing/navigation';
import {Badge} from '../../shared/components/Badge';
import {SLABadge} from './components/SLABadge';
import {useIncidentDetail} from './useIncidentDetail';
import {IncidentEvidence} from './IncidentEvidence';
import {IncidentActions} from './IncidentActions';

export default function IncidentDetail({token,profile,id,staff}:{token:string;profile:Profile;id:string;staff:Row[]}){
 const state=useIncidentDetail(token,id);
 const {data,error}=state;
 if(!data)return <div className={error?'error-box':'w-empty'}>{error||'Đang tải hồ sơ điều tra…'}</div>;
 const r=data.incident,role=profile.role;
 return <><div className="w-detail-head"><button className="secondary" onClick={()=>go(role)}>← Khu vực làm việc</button><h2>{id}</h2><Badge value={r.MucDoNghiemTrong}/><Badge value={r.TrangThai}/><SLABadge incident={r}/></div>{error&&<div className="error-box">{error}</div>}

 <div className="detail-grid"><IncidentEvidence data={data} role={role}/><IncidentActions token={token} profile={profile} staff={staff} state={state} data={data}/></div></>;
}
