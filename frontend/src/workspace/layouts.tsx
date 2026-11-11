// Compatibility exports; implementations live in feature/shared/role modules.
export type {WorkspaceProps} from '../app/types';
export {AdminLayout} from '../roles/admin/Workspace';
export {ManagerLayout} from '../roles/soc-manager/Workspace';
export {AnalystL1Layout} from '../roles/soc-l1/Workspace';
export {AnalystL2Layout} from '../roles/soc-l2/Workspace';
export {AnalystL3Layout} from '../roles/soc-l3/Workspace';
export {ResponderLayout} from '../roles/incident-responder/Workspace';
export {SharedIOC} from '../features/intelligence/SharedIOC';
export {HunterLayout} from '../roles/threat-hunter/Workspace';
export {Personal} from '../features/reporting/Personal';
