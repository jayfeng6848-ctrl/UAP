/**
 * Typed API client tests (Appendix AL §24-§29, §68).
 *
 * Verifies the single owner of: base URL · correlation header · auth transport ·
 * timeout/abort · JSON parsing · error normalisation · one-shot 401 recovery.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createApiClient } from './client';
import { ApiError } from './errors';
import { CORRELATION_HEADER } from './correlation';

/** Deterministic stand-in for `Response` (jsdom does not provide one). */
function makeResponse(
  status: number,
  body?: unknown,
  options: { unreadable?: boolean } = {},
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => {
      if (options.unreadable) {
        throw new SyntaxError('unreadable body');
      }
      return body;
    },
  } as unknown as Response;
}

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function lastCall(): [string, RequestInit] {
  const call = fetchMock.mock.calls.at(-1);
  if (!call) {
    throw new Error('fetch was not called');
  }
  return call as [string, RequestInit];
}

describe('createApiClient transport', () => {
  it('sends a correlation id, JSON accept header and same-origin credentials', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, { ok: true }));
    const client = createApiClient();

    const result = await client.get<{ ok: boolean }>('/api/v1/meta');

    expect(result).toEqual({ ok: true });
    const [url, init] = lastCall();
    expect(url).toBe('/api/v1/meta');
    expect(init.method).toBe('GET');
    expect(init.credentials).toBe('same-origin');
    const headers = init.headers as Record<string, string>;
    expect(headers[CORRELATION_HEADER]).toMatch(/[0-9a-f-]{8,}/i);
    expect(headers.accept).toBe('application/json');
    expect(headers.authorization).toBeUndefined();
    expect(headers['content-type']).toBeUndefined();
  });

  it('attaches the memory token as a bearer header when present', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, {}));
    const client = createApiClient({ getToken: () => 'memory-token' });

    await client.get('/me');

    const headers = lastCall()[1].headers as Record<string, string>;
    expect(headers.authorization).toBe('Bearer memory-token');
  });

  it('serialises query parameters and skips undefined values', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, {}));
    const client = createApiClient({ baseUrl: '/base' });

    await client.get('/employees', { query: { limit: 20, status: 'active', space_id: undefined } });

    expect(lastCall()[0]).toBe('/base/employees?limit=20&status=active');
  });

  it('serialises the body and content-type for POST/PATCH', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(201, { id: 'x' }));
    const client = createApiClient();

    await client.post('/company/employees', { name: 'Ada' });

    const [, init] = lastCall();
    expect(init.method).toBe('POST');
    expect(init.body).toBe(JSON.stringify({ name: 'Ada' }));
    expect((init.headers as Record<string, string>)['content-type']).toBe('application/json');

    fetchMock.mockResolvedValueOnce(makeResponse(200, {}));
    await client.patch('/company/employees/1', { name: 'Grace' });
    expect(lastCall()[1].method).toBe('PATCH');
  });

  it('honours an explicit correlation id override', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, {}));
    const client = createApiClient();

    await client.get('/me', { correlationId: 'trace-123' });

    expect((lastCall()[1].headers as Record<string, string>)[CORRELATION_HEADER]).toBe('trace-123');
  });

  it('returns undefined for 204 responses without parsing a body', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(204));
    const client = createApiClient();

    await expect(client.post('/sessions/logout')).resolves.toBeUndefined();
  });

  it('normalises every frozen HTTP status onto a stable error code', async () => {
    const cases: Array<[number, string]> = [
      [401, 'AUTH_REQUIRED'],
      [403, 'ACCESS_DENIED'],
      [409, 'CONFLICT'],
      [422, 'VALIDATION_OR_NOT_FOUND'],
      [503, 'SERVICE_BOUNDARY_ERROR'],
      [500, 'UNKNOWN_ERROR'],
    ];

    for (const [status, code] of cases) {
      fetchMock.mockResolvedValueOnce(makeResponse(status, { detail: 'safe detail' }));
      const client = createApiClient();
      const error = await client.get('/me').catch((cause: unknown) => cause);
      expect(error).toBeInstanceOf(ApiError);
      const apiError = error as ApiError;
      expect(apiError.status).toBe(status);
      expect(apiError.code).toBe(code);
      expect(apiError.detail).toBe('safe detail');
      expect(apiError.correlationId).toBeTruthy();
      expect(apiError.message).not.toMatch(/sql|constraint|traceback|psycopg/i);
    }
  });

  it('reports an unreadable success body as a safe unknown error', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, undefined, { unreadable: true }));
    const client = createApiClient();

    const error = (await client.get('/me').catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe('UNKNOWN_ERROR');
    expect(error.message).not.toMatch(/SyntaxError|unreadable body/);
  });

  it('reports transport failures as NETWORK_ERROR and keeps the correlation id', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('failed to fetch'));
    const client = createApiClient();

    const error = (await client.get('/me').catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe('NETWORK_ERROR');
    expect(error.status).toBe(0);
    expect(error.correlationId).toBeTruthy();
  });
});

describe('createApiClient 401 recovery', () => {
  it('performs exactly one recovery and retries the original request once', async () => {
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, {}))
      .mockResolvedValueOnce(makeResponse(200, { user_id: 'u-1' }));
    const onUnauthorized = vi.fn(async () => true);
    const client = createApiClient({ onUnauthorized });

    const result = await client.get<{ user_id: string }>('/me');

    expect(result).toEqual({ user_id: 'u-1' });
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const first = fetchMock.mock.calls[0][1] as RequestInit;
    const second = fetchMock.mock.calls[1][1] as RequestInit;
    expect((first.headers as Record<string, string>)[CORRELATION_HEADER]).toBe(
      (second.headers as Record<string, string>)[CORRELATION_HEADER],
    );
  });

  it('never loops: a second 401 after recovery surfaces AUTH_REQUIRED', async () => {
    fetchMock
      .mockResolvedValueOnce(makeResponse(401, {}))
      .mockResolvedValueOnce(makeResponse(401, {}));
    const onUnauthorized = vi.fn(async () => true);
    const client = createApiClient({ onUnauthorized });

    const error = (await client.get('/me').catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe('AUTH_REQUIRED');
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('surfaces AUTH_REQUIRED when recovery fails', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(401, {}));
    const onUnauthorized = vi.fn(async () => false);
    const client = createApiClient({ onUnauthorized });

    const error = (await client.get('/me').catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe('AUTH_REQUIRED');
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });
});

describe('createApiClient cancellation', () => {
  it('propagates a caller abort as a NETWORK_ERROR and passes the signal to fetch', async () => {
    const controller = new AbortController();
    fetchMock.mockImplementationOnce(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
        }),
    );
    const client = createApiClient();

    const pending = client.get('/me', { signal: controller.signal });
    controller.abort();

    const error = (await pending.catch((cause: unknown) => cause)) as ApiError;
    expect(error.code).toBe('NETWORK_ERROR');
    expect((lastCall()[1] as RequestInit).signal).toBeInstanceOf(AbortSignal);
  });

  it('aborts a request that exceeds its timeout', async () => {
    fetchMock.mockImplementationOnce(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
        }),
    );
    const client = createApiClient({ timeoutMs: 5 });

    const error = (await client.get('/me').catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe('NETWORK_ERROR');
  });
});
