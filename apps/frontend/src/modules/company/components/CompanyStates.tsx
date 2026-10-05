import { Button, EmptyState, ErrorState, LoadingState } from '../../../components';
import { messageForCode } from '../../../platform/api';
import type { ApiError } from '../../../platform/api';
import type { ReactNode } from 'react';

import type { ResourceState } from '../hooks';

/** Shown while the tenant context catches up with the address (no API call yet). */
export function TenantResolving() {
  return (
    <div data-testid="company-tenant-resolving">
      <LoadingState label="Resolving tenant context…" />
    </div>
  );
}

export function CompanyLoading({ label = 'Loading…' }: { label?: string }) {
  return <LoadingState label={label} />;
}

export function CompanyEmpty({ title, description }: { title: string; description?: string }) {
  return (
    <div data-testid="company-empty">
      <EmptyState title={title} description={description} />
    </div>
  );
}

/**
 * One error surface for every Company read/mutation failure: the frozen message for
 * the normalised code, an optional correlation reference and a retry affordance.
 * Nothing internal (SQL, table, constraint, stack) is ever rendered.
 */
export function CompanyError({
  error,
  onRetry,
  retryLabel = 'Try again',
}: {
  error: ApiError;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  return (
    <div data-testid="company-error">
      <ErrorState
        message={messageForCode(error.code)}
        correlationId={error.correlationId}
        actions={
          onRetry ? (
            <Button variant="secondary" size="small" onClick={onRetry}>
              {retryLabel}
            </Button>
          ) : undefined
        }
      />
    </div>
  );
}

/**
 * Uniform read-state switch: idle/loading → loading, error → error + retry,
 * empty → the caller's empty state, otherwise the caller's content.
 */
export function CompanyResource<T>({
  state,
  isEmpty,
  empty,
  loadingLabel,
  onRetry,
  children,
}: {
  state: ResourceState<T>;
  isEmpty: (data: T) => boolean;
  empty: ReactNode;
  loadingLabel?: string;
  onRetry: () => void;
  children: (data: T) => ReactNode;
}) {
  if (state.status === 'idle' || state.status === 'loading') {
    return <CompanyLoading label={loadingLabel} />;
  }
  if (state.status === 'error') {
    return <CompanyError error={state.error} onRetry={onRetry} />;
  }
  if (isEmpty(state.data)) {
    return <>{empty}</>;
  }
  return <>{children(state.data)}</>;
}
