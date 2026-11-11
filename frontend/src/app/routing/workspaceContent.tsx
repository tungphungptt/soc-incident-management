import {AnalystIncidentDetail} from '../../features/analysis/AnalystIncidentDetail';
import {ResponseIncidentDetail} from '../../roles/incident-responder/ResponseIncidentDetail';
import React from 'react';
import {Panel} from '../../shared/components/Panel';
import {IncidentTable} from '../../features/incidents/components/IncidentTable';
import {Directory} from '../../features/catalog/Directory';
import IncidentDetail from '../../features/incidents/IncidentDetail';
import {AdminLayout} from '../../roles/admin/Workspace';
import {ManagerLayout} from '../../roles/soc-manager/Workspace';
import {AnalystL1Layout} from '../../roles/soc-l1/Workspace';
import {AnalystL2Layout} from '../../roles/soc-l2/Workspace';
import {AnalystL3Layout} from '../../roles/soc-l3/Workspace';
import {ResponderLayout} from '../../roles/incident-responder/Workspace';
import {HunterLayout} from '../../roles/threat-hunter/Workspace';
import {Personal} from '../../features/reporting/Personal';
import {AdminAudit} from '../../roles/admin/Audit';
import {go} from './navigation';
import {Row} from '../../shared/types';
import {WorkspaceProps} from '../types';

export function workspaceContent({props,forbidden,page,route,admin,roles,audit}:{props:WorkspaceProps;forbidden:boolean;page:string;route:string[];admin:boolean;roles:Row[];audit:Row[]}){
 const {token,profile,incidents,reports,staff,reload,month}=props;
 let content:React.ReactNode;
 if(forbidden)content=<Panel title="Không có quyền"><p>URL này thuộc khu vực vai trò khác hoặc không tồn tại.</p><button className="primary" onClick={()=>go(profile.role)}>Về trang chủ của tôi</button></Panel>;
 else if(page==='personal')content=<Personal token={token} month={month}/>;
 else if(admin&&['to_chuc','tai_san','nhan_vien_soc'].includes(page))content=<Directory key={page} token={token} table={page}/>;
 else if(page==='audit')content=<AdminAudit rows={audit}/>;
 else if(page==='incidents'&&route[2]&&['SOC_L1','SOC_L2','SOC_L3'].includes(profile.role))content=<AnalystIncidentDetail token={token} profile={profile} id={route[2]} staff={staff}/>;
 else if(page==='incidents'&&route[2]&&profile.role==='INCIDENT_RESPONDER')content=<ResponseIncidentDetail token={token} profile={profile} id={route[2]} staff={staff}/>;
 else if(page==='incidents'&&route[2])content=<IncidentDetail token={token} profile={profile} id={route[2]} staff={staff}/>;
 else if(page==='incidents')content=<Panel title={['SOC_L2','INCIDENT_RESPONDER'].includes(profile.role)?'Incident được giao cho tôi':'Tra cứu hồ sơ Incident'}><IncidentTable rows={incidents} role={profile.role}/></Panel>;
 else if(admin)content=<AdminLayout token={token} roles={roles} staff={staff} reload={reload}/>;
 else if(profile.role==='SOC_MANAGER')content=<ManagerLayout {...props}/>;
 else if(profile.role==='SOC_L1')content=<AnalystL1Layout {...props}/>;
 else if(profile.role==='SOC_L2')content=<AnalystL2Layout {...props}/>;
 else if(profile.role==='SOC_L3')content=<AnalystL3Layout {...props}/>;
 else if(profile.role==='INCIDENT_RESPONDER')content=<ResponderLayout {...props}/>;
 else content=<HunterLayout {...props}/>;

 return content;
}
