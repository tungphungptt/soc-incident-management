import React from 'react';
import {useState} from 'react';
import {useFeedback} from '../feedback/FeedbackProvider';

export function ActionForm({onSubmit,children,label='Lưu',className='',disabled=false}:{onSubmit:(data:FormData)=>Promise<any>;children:React.ReactNode;label?:string;className?:string;disabled?:boolean}){
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 const {notify}=useFeedback();
 return <form className={`w-form ${className}`} aria-busy={busy} onSubmit={async e=>{e.preventDefault();const form=e.currentTarget;const data=new FormData(form);setBusy(true);setError('');setMessage('');try{const r=await onSubmit(data);const text=r?.message||'Đã lưu thành công.';setMessage(text);notify(text);}catch(err:any){setError(err.message);notify(err.message,'error')}finally{setBusy(false)}}}>
 {children}{error&&<div className="error-box" role="alert">{error}</div>}{message&&<div className="w-success" role="status">{message}</div>}<button className="primary" disabled={busy||disabled}>{busy?'Đang lưu…':label}</button></form>;
}
