

export function Badge({value}:{value:string}){return <span className={`w-badge badge-${value?.toLowerCase()}`}>{value||'—'}</span>}
