import {Sun,Moon} from 'lucide-react';
import {Button} from '../../shared/components/Button';
import {ThemePreference} from './useTheme';

export function ThemeToggle({theme,setPreference}:{theme:'light'|'dark';setPreference:(value:ThemePreference)=>void}){
 return <Button className="theme-toggle" onClick={()=>setPreference(theme==='dark'?'light':'dark')} aria-label="Chuyển giao diện sáng tối" aria-pressed={theme==='dark'}>{theme==='dark'?<Sun size={18}/>:<Moon size={18}/>} {theme==='dark'?'Sáng':'Tối'}</Button>;
}
