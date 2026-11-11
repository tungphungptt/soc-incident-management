import {createContext, ReactNode, useContext, useEffect, useRef, useState} from 'react';
import {CheckCircle2, AlertCircle, ShieldAlert, X} from 'lucide-react';
import {Button} from '../components/Button';
import {Modal} from '../components/Modal';

type Confirmation = {title: string; description: string; confirmLabel?: string};
type Notice = {id: number; message: string; tone: 'success' | 'error'};
type Feedback = {notify: (message: string, tone?: Notice['tone']) => void; confirm: (options: Confirmation) => Promise<boolean>};
const FeedbackContext = createContext<Feedback | null>(null);

export function FeedbackProvider({children}: {children: ReactNode}) {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null);
  const pending = useRef<((accepted: boolean) => void) | null>(null);
  const sequence = useRef(0);
  const timers = useRef(new Set<ReturnType<typeof setTimeout>>());
  useEffect(() => () => {timers.current.forEach(clearTimeout); pending.current?.(false);}, []);
  const notify: Feedback['notify'] = (message, tone = 'success') => {
    const id = ++sequence.current;
    setNotices(items => [...items.slice(-2), {id, message, tone}]);
    const timer = setTimeout(() => {setNotices(items => items.filter(item => item.id !== id)); timers.current.delete(timer);}, 6000);
    timers.current.add(timer);
  };
  const confirm: Feedback['confirm'] = options => new Promise(resolve => {
    pending.current?.(false);
    pending.current = resolve;
    setConfirmation(options);
  });
  const finish = (accepted: boolean) => {
    const resolve = pending.current;
    pending.current = null;
    setConfirmation(null);
    resolve?.(accepted);
  };
  return <FeedbackContext.Provider value={{notify, confirm}}>
    {children}
    <div className="ui-toast-stack" role="region" aria-label="Thông báo" aria-live="off">
      {notices.map(notice => <div className={`ui-toast ui-toast-${notice.tone}`} key={notice.id}>
        {notice.tone === 'success' ? <CheckCircle2 size={20} aria-hidden="true"/> : <AlertCircle size={20} aria-hidden="true"/>}
        <span>{notice.message}</span><Button variant="ghost" iconOnly aria-label="Đóng thông báo" onClick={() => setNotices(items => items.filter(item => item.id !== notice.id))}><X size={16}/></Button>
      </div>)}
    </div>
    {confirmation && <Modal title={confirmation.title} onClose={() => finish(false)}>
      <div className="ui-confirm-body"><span className="ui-confirm-icon"><ShieldAlert size={24}/></span><p>{confirmation.description}</p></div>
      <div className="ui-modal-actions"><Button autoFocus onClick={() => finish(false)}>Hủy</Button><Button variant="danger" onClick={() => finish(true)}>{confirmation.confirmLabel || 'Xác nhận'}</Button></div>
    </Modal>}
  </FeedbackContext.Provider>;
}

export function useFeedback() {
  const value = useContext(FeedbackContext);
  if (!value) throw new Error('FeedbackProvider is required');
  return value;
}
