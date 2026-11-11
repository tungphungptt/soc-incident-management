
import {roleConfig} from './roles/config';
import {useRoute} from './app/routing/useRoute';
import {workspaceMenu} from './app/routing/menu';
import {workspaceContent} from './app/routing/workspaceContent';
import {useWorkspaceState,useWorkspaceData} from './app/data/useWorkspaceData';
import {useAuthentication} from './app/auth/useAuthentication';
import {LoginScreen} from './app/auth/LoginScreen';
import {useTheme} from './app/theme/useTheme';
import {ThemeToggle} from './app/theme/ThemeToggle';
import {WorkspaceShell} from './app/shell/WorkspaceShell';
import {WorkspaceProps} from './app/types';
import './workspace/workspace.css';

export default function App(){
 const state=useWorkspaceState();
 const route=useRoute();
 const {theme,preference,setPreference}=useTheme();
 const auth=useAuthentication(state);
 const {token,profile,logout}=auth;
 useWorkspaceData(token,profile,route,state);
 const {roles,staff,incidents,reports,month,setMonth,error,loading,setVersion,audit}=state;
 const themeButton=<ThemeToggle theme={theme} setPreference={setPreference}/>;
 if(!token)return <LoginScreen auth={auth} error={error} themeButton={themeButton}/>;
 if(!profile)return <div className="login-screen">{error||'Đang kiểm tra phiên đăng nhập…'}<button className="secondary" onClick={logout}>Đăng nhập lại</button></div>;
 const config=roleConfig[profile.role];if(!config)return <div className="error-box">Vai trò không được hỗ trợ.<button onClick={logout}>Đăng xuất</button></div>;
 const reload=()=>setVersion(v=>v+1),admin=profile.role==='ADMIN';
 const menu=workspaceMenu(profile,config,admin);
 const page=route[1]||'home';const forbidden=route[0]!==profile.role||!menu.some(m=>m.page===page);
 const props:WorkspaceProps={token,profile,incidents,reports,staff,reload,month};
 const content=workspaceContent({props,forbidden,page,route,admin,roles,audit});
 return <WorkspaceShell {...{profile,config,menu,page,forbidden,admin,month,setMonth,preference,setPreference,logout,reload,loading,error,content}}/>;
}
