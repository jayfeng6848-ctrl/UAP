/** Typed error model tests (Appendix AL §28-§29). */

import { describe, expect, it } from 'vitest';

import { ApiError, codeForStatus, messageForCode, normalizeHttpError } from './errors';
import { CORRELATION_HEADER } from './correlation';

function makeResponse(status: number, body: unknown, unreadable = false): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => {
      if (unreadable) {
        throw new SyntaxError('not json');
      }
      return body;
    },
  } as unknown as Response;
}

describe('codeForStatus', () => {
  it('maps the frozen taxonomy', () => {
    expect(codeForStatus(401)).toBe('AUTH_REQUIRED');
    expect(codeForStatus(403)).toBe('ACCESS_DENIED');
    expect(codeForStatus(409)).toBe('CONFLICT');
    expect(codeForStatus(422)).toBe('VALIDATION_OR_NOT_FOUND');
    expect(codeForStatus(503)).toBe('SERVICE_BOUNDARY_ERROR');
  });

  it('falls back to UNKNOWN_ERROR for unmapped statuses', () => {
    expect(codeForStatus(418)).toBe('UNKNOWN_ERROR');
    expect(codeForStatus(500)).toBe('UNKNOWN_ERROR');
  });
});

describe('messageForCode', () => {
  it('always returns a safe, human-readable message', () => {
    for (const code of [
      'AUTH_REQUIRED',
      'ACCESS_DENIED',
      'CONFLICT',
      'VALIDATION_OR_NOT_FOUND',
      'SERVICE_BOUNDARY_ERROR',
      'NETWORK_ERROR',
      'UNKNOWN_ERROR',
    ] as const) {
      const message = messageForCode(code);
      expect(message.length).toBeGreaterThan(0);
      expect(message).not.toMatch(/sql|select |constraint|traceback|psycopg|stack/i);
    }
  });
});

describe('normalizeHttpError', () => {
  it('keeps a short, non-sensitive server detail', async () => {
    const error = await normalizeHttpError(
      makeResponse(403, { detail: 'Permission denied for this tenant.' }),
      'corr-1',
    );

    expect(error.code).toBe('ACCESS_DENIED');
    expect(error.detail).toBe('Permission denied for this tenant.');
    expect(error.correlationId).toBe('corr-1');
  });

  it('drops an over-long (potentially unsafe) detail', async () => {
    const error = await normalizeHttpError(makeResponse(422, { detail: 'x'.repeat(201) }), null);

    expect(error.code).toBe('VALIDATION_OR_NOT_FOUND');
    expect(error.detail).toBeNull();
  });

  it('drops a non-string detail', async () => {
    const error = await normalizeHttpError(makeResponse(409, { detail: { nested: true } }), null);

    expect(error.detail).toBeNull();
  });

  it('tolerates a non-JSON error body', async () => {
    const error = await normalizeHttpError(makeResponse(503, null, true), 'corr-2');

    expect(error.code).toBe('SERVICE_BOUNDARY_ERROR');
    expect(error.detail).toBeNull();
    expect(error.correlationId).toBe('corr-2');
  });
});

describe('ApiError', () => {
  it('exposes status, code, correlation id and detail', () => {
    const error = new ApiError({
      status: 403,
      code: 'ACCESS_DENIED',
      message: 'denied',
      correlationId: 'c',
      detail: 'd',
    });

    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe('ApiError');
    expect(error.status).toBe(403);
    expect(error.code).toBe('ACCESS_DENIED');
    expect(error.correlationId).toBe('c');
    expect(error.detail).toBe('d');
  });

  it('network() is a safe, status-less error', () => {
    const error = ApiError.network('corr-3');
    expect(error.code).toBe('NETWORK_ERROR');
    expect(error.status).toBe(0);
    expect(error.correlationId).toBe('corr-3');
    expect(error.message).toBe('The service could not be reached. Please try again.');
  });
});

describe('correlation header contract', () => {
  it('uses the backend-agreed header name', () => {
    expect(CORRELATION_HEADER).toBe('x-correlation-id');
  });
});
