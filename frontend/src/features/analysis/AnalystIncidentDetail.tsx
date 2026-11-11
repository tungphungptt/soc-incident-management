import {useRef} from 'react';
import IncidentDetail from '../incidents/IncidentDetail';
import {Profile,Row} from '../../shared/types';
import {Button} from '../../shared/components/Button';
import './analyst.css';

/** Presentation wrapper: keep the existing detail hook, permissions and mutations intact. */
export function AnalystIncidentDetail(props:{token:string;profile:Profile;id:string;staff:Row[]}) {
 const root=useRef<HTMLDivElement>(null);
 const sections=[['Hồ sơ','Hồ sơ sự cố'],['Bằng chứng','Cảnh báo liên quan'],['IOC / MITRE','IOC liên quan'],['Lịch sử','Lịch sử xử lý đầy đủ'],['Thao tác',null]] as const;
 const jump=(title:string|null)=>{
  const target=title?Array.from(root.current?.querySelectorAll<HTMLElement>('section.w-panel')||[]).find(panel=>panel.querySelector('h2')?.textContent===title):root.current?.querySelector<HTMLElement>('.detail-actions');
  if(target){target.scrollIntoView({behavior:'smooth',block:'start'});target.tabIndex=-1;target.focus({preventScroll:true});}
 };
 return <div ref={root} className="ui3-detail"><div className="ui3-detail-context"><span>{props.profile.role==='SOC_L1'?'PHÂN LOẠI & CHUYỂN XỬ LÝ':props.profile.role==='SOC_L2'?'INVESTIGATION WORKSPACE':'PHÂN TÍCH CHUYÊN SÂU'}</span><p>Bằng chứng, thông tin kỹ thuật và thao tác theo quyền của bạn.</p></div><nav className="ui3-detail-nav" aria-label="Điều hướng nội dung Incident">{sections.map(([label,title])=><Button key={label} className={title===null?'ui3-actions-jump':undefined} variant="secondary" onClick={()=>jump(title)}>{label}</Button>)}</nav><IncidentDetail {...props}/></div>;
}
