import {post} from '../../shared/api/client';
import {Panel} from '../../shared/components/Panel';
import {ActionForm} from '../../shared/forms/ActionForm';
import {Input,Select} from '../../shared/forms/fields';

export function CreateIOC({token,after}:{token:string;after:()=>void}){return <Panel title="Thêm IOC"><ActionForm label="Lưu IOC" onSubmit={async d=>{const r=await post(token,'/workspace/iocs',Object.fromEntries(d));after();return r;}}><Select label="Loại IOC" name="type" options={['IP','Domain','URL','Hash','Email'].map(v=>({value:v,label:v}))}/><Input name="value" label="Giá trị"/><Input name="source" label="Nguồn"/><Select name="confidence" label="Mức tin cậy" options={['HIGH','MEDIUM','LOW'].map(v=>({value:v,label:v}))}/></ActionForm></Panel>}
