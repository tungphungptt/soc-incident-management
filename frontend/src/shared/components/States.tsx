import {AlertCircle, Inbox, LoaderCircle} from 'lucide-react';
import {Button} from './Button';

export function LoadingState({message = 'Đang tải dữ liệu…'}: {message?: string}) {
  return <div className="ui-state ui-loading" role="status"><LoaderCircle aria-hidden="true" size={24}/><span>{message}</span></div>;
}

export function EmptyState({message = 'Chưa có dữ liệu'}: {message?: string}) {
  return <div className="ui-state ui-empty"><Inbox size={28} aria-hidden="true"/><p>{message}</p></div>;
}

export function ErrorState({message, onRetry}: {message: string; onRetry?: () => void}) {
  return <div className="ui-error" role="alert"><AlertCircle size={20} aria-hidden="true"/><span>{message}</span>{onRetry && <Button onClick={onRetry}>Thử lại</Button>}</div>;
}
