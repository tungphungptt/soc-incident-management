

export function Input({label,name,type='text',required=true,defaultValue,min,max}:{label:string;name:string;type?:string;required?:boolean;defaultValue?:any;min?:number;max?:number}){
 return <label className="w-field"><span>{label}</span><input name={name} type={type} required={required} defaultValue={defaultValue} min={min} max={max}/></label>;
}

export function Select({label,name,options,required=true}:{label:string;name:string;options:{value:string;label:string}[];required?:boolean}){
 return <label className="w-field"><span>{label}</span><select name={name} required={required}>{options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></label>;
}
