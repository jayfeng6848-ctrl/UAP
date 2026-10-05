/**
 * Typed API error model (Appendix AL H05/H09).
 *
 * Normalisation maps the frozen HTTP taxonomy onto stable client codes. The
 * message is always safe for display: SQL, table/constraint names, stack traces,
 * database details and internal exceptions must never reach the browser.
 */

export const API_ERROR_CODES = [
  'AUTH_REQUIRED',
  'ACCESS_DENIED',
  'CONFLICT',
  'VALIDATION_OR_NOT_FOUND',
  'SERVICE_BOUNDARY_ERROR',
  'NETWORK_ERROR',
  'UNKNOWN_ERROR',
] as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[number];

const STATUS_TO_CODE: Record<number, ApiErrorCode> = {
  401: 'AUTH_REQUIRED',
  403: 'ACCESS_DENIED',
  409: 'CONFLICT',
  422: 'VALIDATION_OR_NOT_FOUND',
  503: 'SERVICE_BOUNDARY_ERROR',
};

export function codeForStatus(status: number): ApiErrorCode {
  return STATUS_TO_CODE[status] ?? 'UNKNOWN_ERROR';
}

export interface ApiErrorInit {
  status: number;
  code: ApiErrorCode;
  message: string;
  correlationId?: string | null;
  detail?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode;
  readonly correlationId: string | null;
  /** Safe, server-provided detail when present (already non-sensitive by contract). */
  readonly detail: string | null;

  constructor(init: ApiErrorInit) {
    super(init.message);
    this.name = 'ApiError';
    this.status = init.status;
    this.code = init.code;
    this.correlationId = init.correlationId ?? null;
    this.detail = init.detail ?? null;
  }

  static network(correlationId: string | null): ApiError {
    return new ApiError({
      status: 0,
      code: 'NETWORK_ERROR',
      message: 'The service could not be reached. Please try again.',
      correlationId,
    });
  }
}

/** Human-readable, non-technical message for a normalised error code. */
export function messageForCode(code: ApiErrorCode): string {
  switch (code) {
    case 'AUTH_REQUIRED':
      return 'Your session has ended. Please sign in again.';
    case 'ACCESS_DENIED':
      return 'You do not have access to this resource.';
    case 'CONFLICT':
      return 'This change conflicts with the current state. Reload and try again.';
    case 'VALIDATION_OR_NOT_FOUND':
      return 'The request could not be processed. Check the values and try again.';
    case 'SERVICE_BOUNDARY_ERROR':
      return 'The service is temporarily unavailable. Please try again later.';
    case 'NETWORK_ERROR':
      return 'The service could not be reached. Please try again.';
    default:
      return 'Something went wrong. Please try again.';
  }
}

function safeDetail(payload: unknown): string | null {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === 'string' && detail.length <= 200) {
      return detail;
    }
  }
  return null;
}

export async function normalizeHttpError(
  response: Response,
  correlationId: string | null,
): Promise<ApiError> {
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  const code = codeForStatus(response.status);
  return new ApiError({
    status: response.status,
    code,
    message: messageForCode(code),
    correlationId,
    detail: safeDetail(payload),
  });
}
