/** Empty / loading / error presentation states shared by every future page. */

import type { ReactNode } from 'react';

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <section data-testid="uap-empty-state">
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
    </section>
  );
}

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <p role="status" aria-live="polite" data-testid="uap-loading-state">
      {label}
    </p>
  );
}

export function ErrorState({
  message,
  correlationId,
  actions,
}: {
  message: string;
  correlationId?: string | null;
  actions?: ReactNode;
}) {
  return (
    <section role="alert" data-testid="uap-error-state">
      <p>{message}</p>
      {correlationId ? <p>Reference: {correlationId}</p> : null}
      {actions}
    </section>
  );
}
