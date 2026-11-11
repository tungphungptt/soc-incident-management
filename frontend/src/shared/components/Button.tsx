import {ButtonHTMLAttributes} from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  iconOnly?: boolean;
};

export function Button({variant = 'secondary', iconOnly = false, className = '', type = 'button', ...props}: ButtonProps) {
  return <button type={type} className={`ui-button ui-button-${variant} ${iconOnly ? 'ui-button-icon' : ''} ${className}`} {...props}/>;
}
