import React from 'react';
import {useState} from 'react';
import {api,post} from '../../shared/api/client';
import {Row} from '../../shared/types';
import {DataTable} from '../../shared/components/DataTable';
import {useFeedback} from '../../shared/feedback/FeedbackProvider';
import {Panel} from '../../shared/components/Panel';
import {ActionForm} from '../../shared/forms/ActionForm';
import {Input} from '../../shared/forms/fields';

export function Directory({token,table}:{token:string;table:string}){
 const {confirm,notify}=useFeedback();
 const [meta,setMeta]=useState<Row|null>(null),[rows,setRows]=useState<Row[]>([]),[editing,setEditing]=useState<Row|null>(null),[error,setError]=useState(''),[page,setPage]=useState(1),[total,setTotal]=useState(0);
 const load=async()=>{try{const [m,r]=await Promise.all([api(token,'/meta/tables'),api(token,`/tables/${table}?page=${page}&page_size=20`)]);setMeta(m.find((t:Row)=>t.name===table));setRows(r.items);setTotal(r.total);}catch(e:any){setError(e.message)}};
 React.useEffect(()=>{setEditing(null);load()},[token,table,page]);
 return <Panel title={table==='to_chuc'?'Danh mục tổ chức':table==='tai_san'?'Tài sản CNTT':'Hồ sơ nhân viên SOC'}>
 {error&&<div className="error-box">{error}</div>}
 <div className="directory-grid"><DataTable rows={rows} columns={[
 ...(meta?.columns||[]).map((c:Row)=>({key:c.name,label:c.name,render:(r:Row)=>r[c.name]===null?'—':String(r[c.name])})),
 {key:'actions',label:'Thao tác',render:r=><div className="w-inline"><button type="button" className="secondary" onClick={()=>setEditing(r)}>Sửa</button><button type="button" className="secondary" onClick={async()=>{if(!await confirm({title:'Xóa bản ghi',description:'Bạn có chắc muốn xóa bản ghi này? Dữ liệu sẽ được xóa khỏi hệ thống khi thao tác thành công.',confirmLabel:'Xóa bản ghi'}))return;try{await api(token,`/tables/${table}/${encodeURIComponent(r[meta!.primary_key[0]])}`,{method:'DELETE'});await load();setError('');notify('Đã xóa bản ghi.')}catch(e:any){setError(e.message)}}}>Xóa</button></div>}
 ]} pagination={{page,pageSize:20,total,onPageChange:setPage}}/>

 {meta&&<ActionForm key={table+JSON.stringify(editing)} label={editing?'Lưu chỉnh sửa':'Thêm bản ghi'} onSubmit={async d=>{const payload:Row={};for(const c of meta.columns){if(editing&&c.primary_key||c.autoincrement||c.read_only)continue;const value=d.get(c.name);payload[c.name]=value===''&&c.nullable?null:/int|decimal/i.test(c.type)?Number(value):value;}const key=editing?'/'+encodeURIComponent(editing[meta.primary_key[0]]):'';const r=await post(token,'/tables/'+table+key,payload,editing?'PUT':'POST');setEditing(null);await load();return r;}}>
 <h3>{editing?'Chỉnh sửa':'Thêm mới'}</h3>{meta.columns.filter((c:Row)=>!c.autoincrement&&!c.read_only&&!(editing&&c.primary_key)).map((c:Row)=><Input key={c.name} name={c.name} label={c.name+(c.name==='MaTC'?' (mã tổ chức có thật)':'')} type={/int|decimal/i.test(c.type)?'number':/date/i.test(c.type)?'date':'text'} required={!c.nullable} defaultValue={editing?.[c.name]??''}/>)}{editing&&<button type="button" className="secondary" onClick={()=>setEditing(null)}>Hủy chỉnh sửa</button>}
 </ActionForm>}</div></Panel>;
}
