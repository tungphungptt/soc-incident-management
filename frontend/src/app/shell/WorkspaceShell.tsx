import React, {Dispatch, SetStateAction} from 'react';
import {Shield, RefreshCw, ChevronRight} from 'lucide-react';
import {Profile} from '../../shared/types';
import {roleConfig} from '../../roles/config';
import {go} from '../routing/navigation';
import {WorkspaceMenu} from '../routing/menu';
import {Button} from '../../shared/components/Button';
import {LoadingState, ErrorState} from '../../shared/components/States';
import {AccountMenu} from './AccountMenu';
import {ThemePreference} from '../theme/useTheme';

type ShellProps = {profile: Profile; config: typeof roleConfig[string]; menu: WorkspaceMenu; page: string; forbidden: boolean; admin: boolean; month: string; setMonth: Dispatch<SetStateAction<string>>; preference:ThemePreference;setPreference:(value:ThemePreference)=>void; logout: () => void; reload: () => void; loading: boolean; error: string; content: React.ReactNode};

export function WorkspaceShell({profile, config, menu, page, forbidden, admin, month, setMonth, preference,setPreference, logout, reload, loading, error, content}: ShellProps) {
  const pageTitle = page === 'personal' ? 'Của tôi' : page === 'home' || page === 'intelligence' ? config.title : menu.find(item => item.page === page)?.label || 'Không có quyền';
  return <div className="role-workspace" data-role={profile.role} style={{'--role-accent': config.accent} as React.CSSProperties}>
    <a className="ui-skip-link" href="#workspace-main" onClick={event => {event.preventDefault(); document.getElementById('workspace-main')?.focus();}}>Đến nội dung chính</a>
    <aside className="workspace-sidebar">
      <div className="workspace-brand"><span className="ui-brand-symbol"><Shield size={24}/></span><div><b>SOC<span>OPS</span></b><small>INCIDENT MANAGEMENT</small></div></div>
      <nav aria-label="Điều hướng chính">{menu.map(item => {
        const active = page === item.page && !forbidden;
        return <button type="button" key={item.page} className={`workspace-nav ${active ? 'active' : ''}`} aria-current={active ? 'page' : undefined} onClick={() => go(profile.role, item.page)}><item.icon size={20} aria-hidden="true"/><span>{item.label}</span>{active && <ChevronRight className="ui-nav-chevron" size={16} aria-hidden="true"/>}</button>;
      })}</nav>
      <AccountMenu {...{profile,roleLabel:config.label,preference,setPreference,logout}}/>
    </aside>
    <main className="workspace-main" id="workspace-main" tabIndex={-1}>
      <header className="workspace-header"><div className="ui-header-context"><div className="ui-breadcrumb">Không gian làm việc<ChevronRight size={13} aria-hidden="true"/><span>{config.label}</span></div><strong>{pageTitle}</strong></div>
        <div className="ui-header-actions">{!admin && <label className="month-control">Tháng báo cáo<input aria-label="Tháng báo cáo" type="month" value={month} onChange={event => setMonth(event.target.value)}/></label>}
          <Button variant="ghost" iconOnly aria-label="Làm mới" onClick={reload}><RefreshCw size={19}/></Button>
        </div>
      </header>
      <div className="workspace-content"><div className="workspace-page-head"><div><span className="workspace-kicker">SOC OPERATIONS / {config.label.toUpperCase()}</span><h1>{pageTitle}</h1><p>{page === 'personal' ? 'Thống kê xử lý và thu nhập của chính bạn.' : config.subtitle}</p></div><span className="workspace-status"><i/>{loading ? 'Đang đồng bộ' : 'Dữ liệu từ hệ thống'}</span></div>
        {error && <ErrorState message={error} onRetry={reload}/>}{loading ? <LoadingState message="Đang tải khu vực làm việc…"/> : content}
        <footer className="workspace-footer"><span>SOC OPS · {config.label}</span><span>{profile.username}</span></footer>
      </div>
    </main>
  </div>;
}
