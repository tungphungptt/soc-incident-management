import {ReactNode, useEffect, useId, useRef} from 'react';
import {X} from 'lucide-react';
import {createPortal} from 'react-dom';
import {Button} from './Button';

export function Modal({title, children, onClose}: {title: string; children: ReactNode; onClose: () => void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current!;
    element.showModal();
    return () => {
      element.close();
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return createPortal(<dialog ref={dialog} className="ui-modal" aria-labelledby={titleId} aria-modal="true" onCancel={event => {event.preventDefault(); onClose();}} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const focusable = Array.from(dialog.current!.querySelectorAll<HTMLElement>('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])')).filter(element => element.getClientRects().length > 0);
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (!first) {event.preventDefault(); dialog.current!.focus();}
    else if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) {event.preventDefault(); last.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
  }}>
    <div className="ui-modal-heading"><h2 id={titleId}>{title}</h2><Button variant="ghost" iconOnly aria-label="Đóng hộp thoại" onClick={onClose}><X size={20}/></Button></div>
    {children}
  </dialog>, document.body);
}
