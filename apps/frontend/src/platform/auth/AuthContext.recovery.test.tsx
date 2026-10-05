/**
 * P21-RUT-04 regression tests — session-recovery wiring.
 *
 * These use the REAL platform API client (`createApiClient`) through the REAL
 * `AuthProvider`, with `fetch` mocked. That is the layer where RUT-04 lived: the
 * stub-client tests could never see it, because the defect was the provider's
 * recovery path re-entering itself through the client that called it.
 *
 * Frozen semantics under test: one recovery attempt → refresh succeeds → retry
 * the original request once; refresh fails → deterministic terminal state, never
 * a self-await, never a retry loop.
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../api';
import type { MeResponse } from '../api';
import { AuthProvider, useAuth } from './AuthContext';

function makeResponse(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

const ME: MeResponse = {
  correlation_id: 'corr',
  session_id: 'sess-1',
  device_id: 'dev-1',
  identity_id: 'ident-1',
  user_id: 'user-1',
  tenant_id: 'tenant-1',
  space_id: null,
  subject_type: 'user',
  scope: 'TENANT',
  authentication_assurance: 'session_verified',
};

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function requestsTo(path: string): number {
  return fetchMock.mock.calls.filter((call) => String(call[0]).split('?')[0] === path).length;
}

async function settleWithin<T>(promise: Promise<T>, ms = 1500): Promise<T | 'PENDING'> {
  return Promise.race([
    promise,
    new Promise<'PENDING'>((resolve) => setTimeout(() => resolve('PENDING'), ms)),
  ]);
}

/** Render the provider with the real client and authenticate a real session. */
async function renderAuthenticated() {
  fetchMock
    .mockResolvedValueOnce(makeResponse(201, { token: 'memory-token', user_id: 'user-1' }))
    .mockResolvedValueOnce(makeResponse(200, ME));
  const rendered = renderHook(() => useAuth(), {
    wrapper: ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>,
  });
  await waitFor(() => expect(rendered.result.current.status).toBe('unauthenticated'));
  await act(async () => {
    expect(await rendered.result.current.login('ada', 'secret', 'dev-1')).toBe('authenticated');
  });
  expect(rendered.result.current.status).toBe('authenticated');
  fetchMock.mockClear();
  return rendered;
}

describe('RUT-04 — refresh recovery wiring', () => {
  it('Test 1: a successful refresh retries the original request exactly once', async () => {
    const { result } = await renderAuthenticated();
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValueOnce(makeResponse(200, { session_id: 'sess-1' }))
      .mockResolvedValueOnce(makeResponse(200, ME))
      .mockResolvedValueOnce(makeResponse(200, { items: [], count: 0, limit: 25 }));

    let payload: unknown;
    await act(async () => {
      payload = await result.current.client.get('/company/tenants/t/employees');
    });

    expect(payload).toEqual({ items: [], count: 0, limit: 25 });
    expect(requestsTo('/company/tenants/t/employees')).toBe(2); // original + one retry
    expect(requestsTo('/sessions/refresh')).toBe(1);
    expect(result.current.status).toBe('authenticated');
  });

  it('Test 2: a 401 refresh settles deterministically (no self-await, no second refresh)', async () => {
    const { result } = await renderAuthenticated();
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }));

    const outcome = await settleWithin(
      result.current.client.get('/company/tenants/t/employees').then(
        () => 'resolved' as const,
        (cause: unknown) => (cause instanceof ApiError ? cause.code : 'other-error'),
      ),
    );

    expect(outcome).toBe('AUTH_REQUIRED');
    expect(requestsTo('/company/tenants/t/employees')).toBe(1); // no retry after a failed recovery
    expect(requestsTo('/sessions/refresh')).toBe(1);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    expect(result.current.user).toBeNull();
  });

  it('Test 3: a non-401 refresh failure terminates with an explicit error', async () => {
    const { result } = await renderAuthenticated();
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValueOnce(makeResponse(503, { detail: 'service temporarily unavailable' }));

    const outcome = await settleWithin(
      result.current.client.get('/company/tenants/t/employees').then(
        () => 'resolved' as const,
        (cause: unknown) => (cause instanceof ApiError ? cause.code : 'other-error'),
      ),
    );

    // The caller keeps the ORIGINAL request's error (it was unauthorized); the
    // refresh failure is not surfaced as a different outcome, and it never loops.
    expect(outcome).toBe('AUTH_REQUIRED');
    expect(requestsTo('/company/tenants/t/employees')).toBe(1);
    expect(requestsTo('/sessions/refresh')).toBe(1);
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));
    expect(result.current.user).toBeNull();
  });

  it('Test 4: concurrent unauthorized requests keep the single-flight refresh', async () => {
    const { result } = await renderAuthenticated();
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValue(makeResponse(200, ME));

    let first: unknown;
    let second: unknown;
    await act(async () => {
      [first, second] = await Promise.all([
        result.current.client.get('/company/tenants/t/employees'),
        result.current.client.get('/company/tenants/t/assignments'),
      ]);
    });

    expect(first).not.toBeNull();
    expect(second).not.toBeNull();
    expect(requestsTo('/sessions/refresh')).toBe(1); // one shared refresh, unchanged semantics
    expect(requestsTo('/company/tenants/t/employees')).toBe(2); // original + retry
    expect(requestsTo('/company/tenants/t/assignments')).toBe(2); // original + retry
  });

  it('Test 5: a rejected sign-in settles and returns to a usable state', async () => {
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }))
      .mockResolvedValueOnce(makeResponse(401, { detail: 'authentication failed' }));
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>,
    });
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'));

    const outcome = await settleWithin(
      result.current.login('ada', 'secret', 'unknown-device').then((value) => value),
    );

    expect(outcome).toBe('failed');
    expect(requestsTo('/sessions')).toBe(1);
    expect(requestsTo('/sessions/refresh')).toBe(1);
    expect(result.current.status).toBe('unauthenticated');
    expect(result.current.user).toBeNull();
  });
});
