import React from 'react';

export function Stats({items}:{items:{label:string;value:React.ReactNode;hint?:string}[]}){return <div className="w-stats">{items.map(s=><div className="w-stat" key={s.label}><small>{s.label}</small><strong className={typeof s.value==='string'&&s.value.includes('/')&&s.value.includes(':')?'ui-stat-detail':undefined}>{s.value}</strong>{s.hint&&<span>{s.hint}</span>}</div>)}</div>}
