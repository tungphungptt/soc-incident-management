import {Row,Profile} from '../shared/types';

export type WorkspaceProps={token:string;profile:Profile;incidents:Row[];reports:Row;staff:Row[];reload:()=>void;month:string};
