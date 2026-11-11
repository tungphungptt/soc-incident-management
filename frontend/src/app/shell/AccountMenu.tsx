import {useEffect,useRef,useState} from 'react';
import {ChevronDown,LogOut,Palette,Settings,ShieldCheck,SlidersHorizontal,UserRound} from 'lucide-react';
import {Profile} from '../../shared/types';
import {ThemePreference} from '../theme/useTheme';

type Section='profile'|'settings'|'security'|'customize'|null;
type Props={profile:Profile;roleLabel:string;preference:ThemePreference;setPreference:(value:ThemePreference)=>void;logout:()=>void};

export function AccountMenu({profile,roleLabel,preference,setPreference,logout}:Props){
 const root=useRef<HTMLDivElement>(null),[open,setOpen]=useState(false),[section,setSection]=useState<Section>(null);
 const [reducedMotion,setReducedMotion]=useState(()=>localStorage.getItem('soc_reduced_motion')==='true');
 useEffect(()=>{document.documentElement.classList.toggle('reduce-motion',reducedMotion);localStorage.setItem('soc_reduced_motion',String(reducedMotion))},[reducedMotion]);
 useEffect(()=>{if(!open)return;const close=(event:MouseEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false)};const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')setOpen(false)};document.addEventListener('mousedown',close);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('mousedown',close);document.removeEventListener('keydown',escape)}},[open]);
 const choose=(value:Section)=>{setSection(current=>current===value?null:value)};
 return <div className="account-menu" ref={root}>
  {open&&<div className="account-popover" role="menu" aria-label="Menu tài khoản">
   <button role="menuitem" onClick={()=>choose('profile')}><UserRound size={18}/><span>Hồ sơ</span></button>
   {section==='profile'&&<div className="account-menu-panel"><b>{profile.username}</b><span>{roleLabel}</span></div>}
   <button role="menuitem" onClick={()=>choose('settings')}><Settings size={18}/><span>Cài đặt</span></button>
   {section==='settings'&&<fieldset className="account-menu-panel"><legend><Palette size={16}/> Giao diện</legend>{([['light','Sáng'],['dark','Tối'],['system','Theo hệ thống']] as const).map(([value,label])=><label key={value}><input type="radio" name="theme" checked={preference===value} onChange={()=>setPreference(value)}/>{label}</label>)}</fieldset>}
   <button role="menuitem" onClick={()=>choose('security')}><ShieldCheck size={18}/><span>Bảo mật &amp; đổi mật khẩu</span></button>
   {section==='security'&&<div className="account-menu-panel account-menu-note">Backend chưa hỗ trợ người dùng tự đổi mật khẩu. Quản trị viên vẫn có thể đổi mật khẩu trong quản lý tài khoản.</div>}
   <button role="menuitem" onClick={()=>choose('customize')}><SlidersHorizontal size={18}/><span>Tùy chỉnh</span></button>
   {section==='customize'&&<label className="account-menu-panel account-menu-check"><input type="checkbox" checked={reducedMotion} onChange={event=>setReducedMotion(event.target.checked)}/>Giảm chuyển động giao diện</label>}
   <button role="menuitem" className="account-menu-logout" onClick={logout}><LogOut size={18}/><span>Đăng xuất</span></button>
  </div>}
  <button type="button" className="workspace-user" aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(value=>!value)}><span className="workspace-user-avatar" aria-hidden="true">{profile.username[0].toUpperCase()}</span><span className="workspace-user-copy"><b>{profile.username}</b><small>{roleLabel}</small></span><ChevronDown className={open?'account-chevron open':'account-chevron'} size={18}/></button>
 </div>;
}
