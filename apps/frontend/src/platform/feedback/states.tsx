/** Shared feedback states: inline error, global error and loading indicator. */

import type { ReactNode } from 'react';

export function LoadingIndicator({ label = '正在加载…' }: { label?: string }) {
  return (
    <p role="status" aria-live="polite">
      {label}
    </p>
  );
}

export function InlineError({ children }: { children: ReactNode }) {
  return (
    <p role="alert" data-tone="error">
      {children}
    </p>
  );
}

export function GlobalError({
  message,
  correlationId,
  onRetry,
}: {
  message: string;
  correlationId?: string | null;
  onRetry?: () => void;
}) {
  return (
    <section role="alert" aria-labelledby="uap-global-error-title">
      <h2 id="uap-global-error-title">出现了一点问题</h2>
      <p>{message}</p>
      {correlationId ? <p data-testid="uap-correlation-id">参考编号：{correlationId}</p> : null}
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          重试
        </button>
      ) : null}
    </section>
  );
}
