import {useEffect,useState} from 'react';

export type ThemePreference='light'|'dark'|'system';

export function useTheme(){
 const [preference,setPreference]=useState<ThemePreference>(()=>{
  const saved=localStorage.getItem('soc_theme');return saved==='dark'||saved==='system'?saved:'light';
 });
 const [systemDark,setSystemDark]=useState(()=>matchMedia('(prefers-color-scheme: dark)').matches);
 useEffect(()=>{const media=matchMedia('(prefers-color-scheme: dark)');const change=()=>setSystemDark(media.matches);media.addEventListener('change',change);return()=>media.removeEventListener('change',change)},[]);
 const theme=preference==='system'?(systemDark?'dark':'light'):preference;
 useEffect(()=>{document.documentElement.dataset.theme=theme;localStorage.setItem('soc_theme',preference)},[theme,preference]);
 return {theme,preference,setPreference};
}
