import {useEffect,useState} from 'react';
import {Clock} from 'lucide-react';
import {Row} from '../../../shared/types';
import {date} from '../../../shared/format';

export function SLABadge({incident}:{incident:Row}){
 const [now,setNow]=useState(Date.now());useEffect(()=>{const id=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(id)},[]);
 const s=incident.sla;if(!s)return <span>—</span>;
 const seconds=s.closed?s.remaining_seconds:Math.floor((new Date(s.deadline).getTime()-now)/1000);
 const min=Math.floor(Math.abs(seconds)/60);const text=`${Math.floor(min/60)}h ${min%60}m ${Math.abs(seconds)%60}s`;
 return <span className={`w-sla ${seconds<0?'breached':''}`} title={`Hạn: ${date(s.deadline)}`}><Clock size={12}/>{s.closed?(seconds<0?'Đã vi phạm':'Đóng đúng hạn'):seconds<0?'Quá hạn':'Còn'} {s.closed&&seconds>=0?'':text}<small>Hạn {date(s.deadline)}</small></span>;
}
