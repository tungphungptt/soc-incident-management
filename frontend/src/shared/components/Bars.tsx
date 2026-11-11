import {EmptyState} from './States';

export function Bars({data, color}: {data: {label: string; value: number}[]; color?: string}) {
  const max = Math.max(1, ...data.map(item => item.value));
  return <figure className="ui-chart" aria-label="Biểu đồ thanh">
    <figcaption className="ui-chart-caption"><i style={{background: color}}/>Giá trị theo từng mục</figcaption>
    <div className="w-bars">{data.map(item => <div className="w-bar" key={item.label} title={`${item.label}: ${item.value}`}><span>{item.label}</span><div><i style={{width: `${item.value / max * 100}%`, background: color}}/></div><b>{item.value}</b></div>)}</div>
    {!data.length && <EmptyState/>}
  </figure>;
}
