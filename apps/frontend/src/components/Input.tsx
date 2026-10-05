import type { InputHTMLAttributes } from 'react';

import styles from './Input.module.css';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export function Input({ invalid = false, className, ...rest }: InputProps) {
  return (
    <input
      {...rest}
      aria-invalid={invalid || undefined}
      className={[styles.input, invalid ? styles.invalid : null, className]
        .filter(Boolean)
        .join(' ')}
    />
  );
}
