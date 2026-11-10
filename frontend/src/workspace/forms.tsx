import React,{useState} from 'react';
import {api,post,Row} from './api';
import {Panel} from './components';

export function ActionForm({onSubmit,children,label='Lưu',className='',disabled=false}:{onSubmit:(data:FormData)=>Promise<any>;children:React.ReactNode;label?:string;className?:string;disabled?:boolean}){
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 return <form className={`w-form ${className}`} onSubmit={async e=>{e.preventDefault();const form=e.currentTarget;const data=new FormData(form);setBusy(true);setError('');setMessage('');try{const r=await onSubmit(data);setMessage(r?.message||'Đã lưu thành công.');}catch(err:any){setError(err.message)}finally{setBusy(false)}}}>
 {children}{error&&<div className="error-box" role="alert">{error}</div>}{message&&<div className="w-success" role="status">{message}</div>}<button className="primary" disabled={busy||disabled}>{busy?'Đang lưu…':label}</button></form>;
}
export function Input({label,name,type='text',required=true,defaultValue,min,max}:{label:string;name:string;type?:string;required?:boolean;defaultValue?:any;min?:number;max?:number}){
 return <label className="w-field"><span>{label}</span><input name={name} type={type} required={required} defaultValue={defaultValue} min={min} max={max}/></label>;
}
export function Select({label,name,options,required=true}:{label:string;name:string;options:{value:string;label:string}[];required?:boolean}){
 return <label className="w-field"><span>{label}</span><select name={name} required={required}>{options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></label>;
}
export function StaffSelect({staff,name='employee_id',filter}:{staff:Row[];name?:string;filter?:string[]}){
 return <Select label="Nhân viên" name={name} options={[{value:'',label:'Chọn nhân viên'},...staff.filter(s=>!filter||filter.includes(s.role)).map(s=>({value:s.employee_id,label:`${s.name} · ${s.role}`}))]}/>;
}
export function CreateIncident({token,staff,alertIds=[],after}:{token:string;staff:Row[];alertIds?:string[];after:()=>void}){
 return <Panel title={alertIds.length?`Gom ${alertIds.length} cảnh báo`:'Tạo Incident từ phát hiện'}><ActionForm label="Tạo sự cố NEW" onSubmit={async d=>{if(d.get('severity')==='CRITICAL'&&!d.get('expert_id'))throw new Error('Incident Critical bắt buộc chọn chuyên gia L2/L3.');const r=await post(token,'/workspace/incidents',{description:d.get('description'),severity:d.get('severity'),expert_id:d.get('expert_id')||null,alert_ids:alertIds});after();return r;}}>
 <Input label="Mô tả phát hiện" name="description"/><Select label="Mức độ nghiêm trọng" name="severity" options={['LOW','MEDIUM','HIGH','CRITICAL'].map(s=>({value:s,label:s}))}/>
 <Select label="Chuyên gia L2/L3 (bắt buộc với Critical)" name="expert_id" required={false} options={[{value:'',label:'Chưa chọn'},...staff.filter(s=>['SOC_L2','SOC_L3'].includes(s.role)).map(s=>({value:s.employee_id,label:s.name+' · '+s.role}))]}/>
 </ActionForm></Panel>;
}
export function CreateIOC({token,after}:{token:string;after:()=>void}){return <Panel title="Thêm IOC"><ActionForm label="Lưu IOC" onSubmit={async d=>{const r=await post(token,'/workspace/iocs',Object.fromEntries(d));after();return r;}}><Select label="Loại IOC" name="type" options={['IP','Domain','URL','Hash','Email'].map(v=>({value:v,label:v}))}/><Input name="value" label="Giá trị"/><Input name="source" label="Nguồn"/><Select name="confidence" label="Mức tin cậy" options={['HIGH','MEDIUM','LOW'].map(v=>({value:v,label:v}))}/></ActionForm></Panel>}

export function Directory({token,table}:{token:string;table:string}){
 const [meta,setMeta]=useState<Row|null>(null),[rows,setRows]=useState<Row[]>([]),[editing,setEditing]=useState<Row|null>(null),[error,setError]=useState(''),[page,setPage]=useState(1),[total,setTotal]=useState(0);
 const load=async()=>{try{const [m,r]=await Promise.all([api(token,'/meta/tables'),api(token,`/tables/${table}?page=${page}&page_size=20`)]);setMeta(m.find((t:Row)=>t.name===table));setRows(r.items);setTotal(r.total);}catch(e:any){setError(e.message)}};
 React.useEffect(()=>{setEditing(null);load()},[token,table,page]);
 return <Panel title={table==='to_chuc'?'Danh mục tổ chức':table==='tai_san'?'Tài sản CNTT':'Hồ sơ nhân viên SOC'}>
 {error&&<div className="error-box">{error}</div>}
 <div className="directory-grid"><div className="w-table-scroll"><table className="w-table"><thead><tr>{meta?.columns.map((c:Row)=><th key={c.name}>{c.name}</th>)}<th>Thao tác</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{meta?.columns.map((c:Row)=><td key={c.name}>{r[c.name]===null?'—':String(r[c.name])}</td>)}<td><div className="w-inline"><button className="secondary" onClick={()=>setEditing(r)}>Sửa</button><button className="secondary" onClick={async()=>{if(!confirm('Xóa bản ghi này?'))return;try{await api(token,`/tables/${table}/${encodeURIComponent(r[meta!.primary_key[0]])}`,{method:'DELETE'});await load();setError('')}catch(e:any){setError(e.message)}}}>Xóa</button></div></td></tr>)}</tbody></table><div className="w-inline w-pagination"><button className="secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Trước</button><span>Trang {page} · {total} bản ghi</span><button className="secondary" disabled={page*20>=total} onClick={()=>setPage(p=>p+1)}>Sau</button></div></div>
 {meta&&<ActionForm key={table+JSON.stringify(editing)} label={editing?'Lưu chỉnh sửa':'Thêm bản ghi'} onSubmit={async d=>{const payload:Row={};for(const c of meta.columns){if(editing&&c.primary_key||c.autoincrement||c.read_only)continue;const value=d.get(c.name);payload[c.name]=value===''&&c.nullable?null:/int|decimal/i.test(c.type)?Number(value):value;}const key=editing?'/'+encodeURIComponent(editing[meta.primary_key[0]]):'';const r=await post(token,'/tables/'+table+key,payload,editing?'PUT':'POST');setEditing(null);await load();return r;}}>
 <h3>{editing?'Chỉnh sửa':'Thêm mới'}</h3>{meta.columns.filter((c:Row)=>!c.autoincrement&&!c.read_only&&!(editing&&c.primary_key)).map((c:Row)=><Input key={c.name} name={c.name} label={c.name+(c.name==='MaTC'?' (mã tổ chức có thật)':'')} type={/int|decimal/i.test(c.type)?'number':/date/i.test(c.type)?'date':'text'} required={!c.nullable} defaultValue={editing?.[c.name]??''}/>)}{editing&&<button type="button" className="secondary" onClick={()=>setEditing(null)}>Hủy chỉnh sửa</button>}
 </ActionForm>}</div></Panel>;
}
