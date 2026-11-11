import {LayoutDashboard,ClipboardList,UserRound,Building2,Monitor,Users,History,Fingerprint} from 'lucide-react';
import {Profile} from '../../shared/types';
import {roleConfig} from '../../roles/config';

export function workspaceMenu(profile:Profile,config:typeof roleConfig[string],admin:boolean){
 const menu=admin?[{page:'home',label:'Tài khoản & phân quyền',icon:Users},{page:'to_chuc',label:'Tổ chức',icon:Building2},{page:'tai_san',label:'Tài sản CNTT',icon:Monitor},{page:'nhan_vien_soc',label:'Nhân viên SOC',icon:UserRound},{page:'audit',label:'Nhật ký hoạt động',icon:History}]:[{page:'home',label:config.title,icon:LayoutDashboard},{page:'incidents',label:'Hồ sơ Incident',icon:ClipboardList},...(profile.role==='THREAT_HUNTER'?[{page:'intelligence',label:'Tra cứu IOC / MITRE',icon:Fingerprint}]:[]),{page:'personal',label:'Của tôi',icon:UserRound}];
 return menu;
}

export type WorkspaceMenu=ReturnType<typeof workspaceMenu>;
