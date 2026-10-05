/**
 * Auth context tests (Appendix AL §19-§23, §53).
 *
 * Reuses the existing /sessions · /me contract, keeps the token in memory only and
 * performs at most one controlled refresh attempt.
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { AuthProvider, useAuth } from './AuthContext';
import { ApiError } from '../api';
import type { ApiClient, MeResponse } from '../api';

const ME: MeResponse = {
  correlation_id: 'corr',
  session_id: 'sess-1',
  device_id: 'dev-1',
  identity_id: 'ident-1',
  user_id: 'user-1',
  tenant_id: null,
  space_id: null,
  subject_type: 'user',
  scope: null,
  authentication_assurance: 'verified_device',
};

interface StubClient {
  client: ApiClient;
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
}

function makeStubClient(): StubClient {
  const get = vi.fn();
  const post = vi.fn();
  const patch = vi.fn();
  const request = vi.fn();
  return { client: { get, post, patch, request } as unknown as ApiClient, get, post };
}

function renderAuth(client: ApiClient) {
  return renderHook(() => useAuth(), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <AuthProvider client={client}>{children}</AuthProvider>
    ),
  });
}

describe('AuthProvider bootstrap', () => {
  it('starts unauthenticated with no token and never calls the API', async () => {
    const stub = makeStubClient();
    const { result } = renderAuth(stub.client);

    // A fresh page load starts from `bootstrapping`/`unauthenticated` — the token is
    // memory-only, so there is no persisted session to restore.
    expect(['bootstrapping', 'unauthenticated']).toContain(result.current.status);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    expect(result.current.user).toBeNull();
    expect(stub.get).not.toHaveBeenCalled();
  });

  it('persists nothing in localStorage/sessionStorage', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    await act(async () => {
      await result.current.login('ada', 'secret');
    });

    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });
});

describe('AuthProvider login', () => {
  it('authenticates when the platform issues a session token', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    let outcome: string | undefined;
    await act(async () => {
      outcome = await result.current.login('ada', 'secret');
    });

    expect(outcome).toBe('authenticated');
    expect(result.current.status).toBe('authenticated');
    expect(result.current.user?.user_id).toBe('user-1');
    expect(stub.post).toHaveBeenCalledWith('/sessions', { login: 'ada', password: 'secret' });
    expect(stub.get).toHaveBeenCalledWith('/me');
  });

  it('reports device_required when no token is issued (unverified device)', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({
      user_id: 'user-1',
      identity_id: 'ident-1',
      authentication_assurance: 'password',
    });
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    let outcome: string | undefined;
    await act(async () => {
      outcome = await result.current.login('ada', 'secret');
    });

    expect(outcome).toBe('device_required');
    expect(result.current.status).toBe('unauthenticated');
    expect(stub.get).not.toHaveBeenCalled();
  });

  it('reports failure and keeps a safe error when sign-in is refused', async () => {
    const stub = makeStubClient();
    stub.post.mockRejectedValueOnce(
      new ApiError({ status: 401, code: 'AUTH_REQUIRED', message: 'nope' }),
    );
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    let outcome: string | undefined;
    await act(async () => {
      outcome = await result.current.login('ada', 'wrong');
    });

    expect(outcome).toBe('failed');
    expect(result.current.status).toBe('unauthenticated');
    expect(result.current.error?.code).toBe('AUTH_REQUIRED');
  });
});

describe('AuthProvider refresh', () => {
  it('de-duplicates concurrent refreshes into a single attempt', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValue({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValue(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    await act(async () => {
      await result.current.login('ada', 'secret');
    });

    let first: boolean | undefined;
    let second: boolean | undefined;
    await act(async () => {
      [first, second] = await Promise.all([result.current.refresh(), result.current.refresh()]);
    });

    expect(first).toBe(true);
    expect(second).toBe(true);
    const refreshCalls = stub.post.mock.calls.filter((call) => call[0] === '/sessions/refresh');
    expect(refreshCalls).toHaveLength(1);
  });

  it('clears auth state when refresh fails', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    await act(async () => {
      await result.current.login('ada', 'secret');
    });
    expect(result.current.status).toBe('authenticated');

    stub.post.mockRejectedValueOnce(new ApiError({ status: 401, code: 'AUTH_REQUIRED', message: 'no' }));
    let recovered: boolean | undefined;
    await act(async () => {
      recovered = await result.current.refresh();
    });

    expect(recovered).toBe(false);
    expect(result.current.status).toBe('unauthenticated');
    expect(result.current.user).toBeNull();
  });
});

describe('AuthProvider logout', () => {
  it('calls /sessions/logout and clears identity state', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    await act(async () => {
      await result.current.login('ada', 'secret');
    });

    stub.post.mockResolvedValueOnce({ revoked: 1 });
    await act(async () => {
      await result.current.logout();
    });

    expect(stub.post).toHaveBeenCalledWith('/sessions/logout', undefined);
    expect(result.current.status).toBe('unauthenticated');
    expect(result.current.user).toBeNull();
  });

  it('clears local state even when the logout call fails', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(ME);
    const { result } = renderAuth(stub.client);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    await act(async () => {
      await result.current.login('ada', 'secret');
    });

    stub.post.mockRejectedValueOnce(ApiError.network('corr'));
    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.status).toBe('unauthenticated');
    expect(result.current.user).toBeNull();
  });
});

describe('useAuth', () => {
  it('throws when used outside AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrowError(/AuthProvider/);
  });
});
