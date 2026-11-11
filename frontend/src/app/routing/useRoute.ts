import {useEffect,useState} from 'react';

export function useRoute(){const [route,setRoute]=useState(location.hash.slice(2).split('/'));useEffect(()=>{const change=()=>setRoute(location.hash.slice(2).split('/'));window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change)},[]);return route;}
