/**
 * Company data hooks (module-local, built on the platform API client).
 *
 * Deliberately tiny: one read hook and one action hook. They add no caching layer
 * and no global store (Appendix AL H06) — server data stays in the component that
 * asked for it, keyed by the tenant so a tenant switch cannot leak old data.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError } from '../../platform/api';

export type ResourceState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; data: T }
  | { status: 'error'; error: ApiError };

/**
 * Runs `load` whenever `deps` change. Pass `null` for `load` to stay idle — that is
 * how Company pages express "tenant not resolved yet, do not touch the API".
 */
export function useApiResource<T>(
  load: ((signal: AbortSignal) => Promise<T>) | null,
  deps: readonly unknown[],
): { state: ResourceState<T>; reload: () => void } {
  const loadRef = useRef(load);
  loadRef.current = load;
  const [nonce, setNonce] = useState(0);
  const [state, setState] = useState<ResourceState<T>>(
    load === null ? { status: 'idle' } : { status: 'loading' },
  );

  useEffect(() => {
    const current = loadRef.current;
    if (current === null) {
      setState({ status: 'idle' });
      return undefined;
    }
    const controller = new AbortController();
    let active = true;
    setState({ status: 'loading' });
    current(controller.signal).then(
      (data) => {
        if (active) {
          setState({ status: 'ready', data });
        }
      },
      (cause: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        setState({
          status: 'error',
          error: cause instanceof ApiError ? cause : ApiError.network(null),
        });
      },
    );
    return () => {
      active = false;
      controller.abort();
    };
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { state, reload };
}

export interface ActionState {
  pending: boolean;
  error: ApiError | null;
  /** Returns true on success; concurrent invocations are ignored (duplicate-click guard). */
  run: (action: () => Promise<void>) => Promise<boolean>;
  clearError: () => void;
}

/** Mutation helper: pending flag, safe error object and duplicate-click protection. */
export function useAction(): ActionState {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const inFlight = useRef(false);

  const clearError = useCallback(() => setError(null), []);

  const run = useCallback(async (action: () => Promise<void>): Promise<boolean> => {
    if (inFlight.current) {
      return false;
    }
    inFlight.current = true;
    setPending(true);
    setError(null);
    try {
      await action();
      return true;
    } catch (cause) {
      setError(cause instanceof ApiError ? cause : ApiError.network(null));
      return false;
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }, []);

  return { pending, error, run, clearError };
}
