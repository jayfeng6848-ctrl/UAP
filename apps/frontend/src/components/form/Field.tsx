import { useId } from 'react';
import type { ReactNode } from 'react';

import { Input } from '../Input';

export interface FieldErrorProps {
  id: string;
  children: ReactNode;
}

export function FieldError({ id, children }: FieldErrorProps) {
  return (
    <p id={id} role="alert" data-testid="uap-field-error">
      {children}
    </p>
  );
}

export interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  children: (ids: { id: string; describedBy: string | undefined; invalid: boolean }) => ReactNode;
}

/**
 * Form field boundary: owns label/control association and error wiring so every
 * future form is accessible by construction (label `for`, `aria-describedby`).
 */
export function Field({ label, error, hint, children }: FieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ');

  return (
    <div>
      <label htmlFor={id}>{label}</label>
      {hint ? <p id={hintId}>{hint}</p> : null}
      {children({ id, describedBy: describedBy || undefined, invalid: Boolean(error) })}
      {error ? <FieldError id={errorId}>{error}</FieldError> : null}
    </div>
  );
}

/** Convenience wrapper for the common single-line text field. */
export function TextField({
  label,
  value,
  onChange,
  error,
  type = 'text',
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  type?: 'text' | 'password';
  placeholder?: string;
}) {
  return (
    <Field label={label} error={error}>
      {({ id, describedBy, invalid }) => (
        <Input
          id={id}
          type={type}
          value={value}
          placeholder={placeholder}
          invalid={invalid}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </Field>
  );
}
