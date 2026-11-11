import {useRef} from 'react';
import IncidentDetail from '../../features/incidents/IncidentDetail';
import {Profile,Row} from '../../shared/types';
import {Button} from '../../shared/components/Button';
import './ui4.css';

export function ResponseIncidentDetail(props:{token:string;profile:Profile;id:string;staff:Row[]}) {
 const root=useRef<HTMLDivElement>(null);
 const jump=(title:string|null)=>{const target=title?Array.from(root.current?.querySelectorAll<HTMLElement>('section.w-panel')||[]).find(panel=>panel.querySelector('h2')?.textContent===title):root.current?.querySelector<HTMLElement>('.detail-actions');if(target){target.scrollIntoView({behavior:'smooth',block:'start'});target.tabIndex=-1;target.focus({preventScroll:true});}};
 return <div ref={root} className="ui4-response-detail"><div className="ui4-detail-heading"><span>INCIDENT RESPONSE WORKSPACE</span><h2>Hành động, bằng chứng và tiến độ xử lý</h2><p>Chỉ các thao tác được phép ở trạng thái hiện tại mới được hiển thị.</p></div><nav className="ui4-detail-nav" aria-label="Điều hướng hồ sơ ứng phó">{[['Hồ sơ','Hồ sơ sự cố'],['Bằng chứng','Cảnh báo liên quan'],['IOC / MITRE','IOC liên quan'],['Lịch sử','Lịch sử xử lý đầy đủ']].map(([label,title])=><Button key={label} variant="secondary" onClick={()=>jump(title)}>{label}</Button>)}<Button className="ui4-actions-jump" variant="primary" onClick={()=>jump(null)}>Thao tác xử lý</Button></nav><IncidentDetail {...props}/></div>;
}
