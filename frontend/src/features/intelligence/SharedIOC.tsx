import {Row} from '../../shared/types';
import {go} from '../../app/routing/navigation';
import {DataTable} from '../../shared/components/DataTable';

export function SharedIOC({rows,role}:{rows:Row[];role:string}){return <DataTable rows={rows} columns={[{key:'type',label:'Loại'},{key:'ioc',label:'IOC chung'},{key:'count',label:'Số Incident'},{key:'incidents',label:'Incident',render:r=><div className="w-chips">{r.incidents.map((id:string)=><button className="text-link" key={id} onClick={()=>go(role,'incidents/'+id)}>{id}</button>)}</div>} ]}/>}
