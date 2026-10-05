import type { SelectHTMLAttributes } from 'react';

import styles from './Select.module.css';

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export function Select({ className, children, ...rest }: SelectProps) {
  return (
    <select {...rest} className={[styles.select, className].filter(Boolean).join(' ')}>
      {children}
    </select>
  );
}
