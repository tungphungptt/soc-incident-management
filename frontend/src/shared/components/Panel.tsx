import React from 'react';

export function Panel({title,children,action,className=''}:{title:string;children:React.ReactNode;action?:React.ReactNode;className?:string}){
 return <section className={`w-panel ${className}`}><div className="w-panel-title"><h2>{title}</h2>{action}</div>{children}</section>;
}
