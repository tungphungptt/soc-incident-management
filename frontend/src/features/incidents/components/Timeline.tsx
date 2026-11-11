import {Row} from '../../../shared/types';
import {date} from '../../../shared/format';

export function Timeline({events}:{events:Row[]}){return <ol className="w-timeline">{events.map((e,i)=><li key={i}><span className="timeline-dot"/><div><time>{date(e.time)}</time><b>{e.title}</b><small>{e.employee}{e.minutes?` · ${e.minutes} phút`:''}</small></div></li>)}{!events.length&&<li>Chưa có lịch sử xử lý.</li>}</ol>}
