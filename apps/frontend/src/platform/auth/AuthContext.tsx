/**
 * Authentication context (Appendix AL H04/H19-H23).
 *
 * Reuses the existing platform identity/session system — no second authentication
 * system, no fake sessions, no employee login. The session token is kept **in
 * memory only** and is never written to localStorage/sessionStorage.
 *
 * Contract facts (verified against apps/api/routes):
 *   POST /sessions          {login, password, device_id?} → token only with a verified device
 *   POST /sessions/refresh  (Bearer) → session/expiry view
 *   POST /sessions/logout   (Bearer) → {"revoked": n}
 *   GET  /me                (Bearer) → frozen log-safe context (no permission set)
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';

import { ApiError, createApiClient } from '../api';
import type { ApiClient, LoginResponse, LogoutResponse, MeResponse } from '../api';

export type AuthStatus = 'bootstrapping' | 'unauthenticated' | 'refreshing' | 'authenticated';

export type LoginOutcome = 'authenticated' | 'device_required' | 'failed';

export interface AuthContextValue {
  status: AuthStatus;
  user: MeResponse | null;
  error: ApiError | null;
  /**
   * The single platform API client (Appendix AL H05).
   *
   * Domain modules consume this client instead of creating their own: it already
   * carries the memory-only session token, the correlation header and the
   * one-shot 401 recovery. No second client, no token accessor is exported.
   */
  client: ApiClient;
  login: (loginId: string, password: string, deviceId?: string) => Promise<LoginOutcome>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  client,
}: {
  children: ReactNode;
  /** Injectable for tests; the default client is memory-token aware. */
  client?: ApiClient;
}) {
  const tokenRef = useRef<string | null>(null);
  /** Latest client, used by the recovery callback (avoids an api↔refresh cycle). */
  const clientRef = useRef<ApiClient | null>(null);
  const [status, setStatus] = useState<AuthStatus>('bootstrapping');
  const [user, setUser] = useState<MeResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const refreshInFlight = useRef<Promise<boolean> | null>(null);

  const fetchMe = useCallback(async (api: ApiClient): Promise<MeResponse | null> => {
    try {
      const me = await api.get<MeResponse>('/me');
      setUser(me);
      setError(null);
      setStatus('authenticated');
      return me;
    } catch (cause) {
      const apiError = cause instanceof ApiError ? cause : null;
      setUser(null);
      setError(apiError);
      setStatus('unauthenticated');
      return null;
    }
  }, []);

  /** At most one controlled recovery: the client retries once and never loops. */
  const refreshInternal = useCallback(async (): Promise<boolean> => {
    if (refreshInFlight.current) {
      return refreshInFlight.current;
    }
    const attempt = (async (): Promise<boolean> => {
      const api = clientRef.current;
      if (api === null) {
        return false;
      }
      setStatus((current) => (current === 'authenticated' ? 'refreshing' : current));
      try {
        await api.post('/sessions/refresh', undefined);
        const me = await fetchMe(api);
        return me !== null;
      } catch {
        tokenRef.current = null;
        setUser(null);
        setStatus('unauthenticated');
        return false;
      } finally {
        refreshInFlight.current = null;
      }
    })();
    refreshInFlight.current = attempt;
    return attempt;
  }, [fetchMe]);

  const api = useMemo<ApiClient>(() => {
    if (client) {
      return client;
    }
    return createApiClient({
      getToken: () => tokenRef.current,
      onUnauthorized: () => refreshInternal(),
    });
  }, [client, refreshInternal]);

  useEffect(() => {
    clientRef.current = api;
  }, [api]);

  useEffect(() => {
    // Tokens are memory-only, so a fresh page load starts unauthenticated by design.
    if (tokenRef.current === null) {
      setStatus('unauthenticated');
      return;
    }
    void fetchMe(api);
  }, [api, fetchMe]);

  const login = useCallback(
    async (loginId: string, password: string, deviceId?: string): Promise<LoginOutcome> => {
      setError(null);
      try {
        const body: Record<string, string> = { login: loginId, password };
        if (deviceId) {
          body.device_id = deviceId;
        }
        const result = await api.post<LoginResponse>('/sessions', body);
        if (!result.token) {
          // The platform issues a session only for a verified device (see /sessions contract).
          setStatus('unauthenticated');
          return 'device_required';
        }
        tokenRef.current = result.token;
        const me = await fetchMe(api);
        return me === null ? 'failed' : 'authenticated';
      } catch (cause) {
        setError(cause instanceof ApiError ? cause : null);
        setStatus('unauthenticated');
        return 'failed';
      }
    },
    [api, fetchMe],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      if (tokenRef.current) {
        await api.post<LogoutResponse>('/sessions/logout', undefined);
      }
    } catch {
      // Logout is best-effort: local state is cleared regardless.
    } finally {
      tokenRef.current = null;
      setUser(null);
      setError(null);
      setStatus('unauthenticated');
    }
  }, [api]);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, error, client: api, login, logout, refresh: refreshInternal }),
    [status, user, error, api, login, logout, refreshInternal],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
