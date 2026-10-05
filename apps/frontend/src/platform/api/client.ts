/**
 * UAP typed API client (Appendix AL H05).
 *
 * Native `fetch` only — no Axios, no wrapper framework. One place owns:
 * base URL · auth transport · correlation header · timeout/abort · JSON parsing ·
 * typed responses · error normalisation · at most one controlled 401 recovery.
 *
 * The client never holds credentials in storage: the token is supplied by the
 * caller (memory-only, see AuthProvider).
 */

import { CORRELATION_HEADER, newCorrelationId } from './correlation';
import { ApiError, normalizeHttpError } from './errors';

export type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export interface RequestOptions {
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  signal?: AbortSignal;
  /** Override the generated correlation id (e.g. to continue an existing trace). */
  correlationId?: string;
}

export interface ApiClientOptions {
  /** Same-origin by default (production reverse proxy; dev uses the Vite proxy). */
  baseUrl?: string;
  timeoutMs?: number;
  /** Memory-only token accessor. */
  getToken?: () => string | null;
  /** Exactly one recovery attempt is made when the server answers 401. */
  onUnauthorized?: () => Promise<boolean>;
}

export interface ApiClient {
  get<T>(path: string, options?: RequestOptions): Promise<T>;
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T>;
  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T>;
  request<T>(method: HttpMethod, path: string, options?: RequestOptions): Promise<T>;
}

const DEFAULT_TIMEOUT_MS = 15_000;

function buildUrl(baseUrl: string, path: string, query?: RequestOptions['query']): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) {
      search.set(key, String(value));
    }
  }
  const suffix = search.toString();
  return `${baseUrl}${path}${suffix ? `?${suffix}` : ''}`;
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  const baseUrl = options.baseUrl ?? '';
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  async function execute<T>(
    method: HttpMethod,
    path: string,
    requestOptions: RequestOptions,
    allowRecovery: boolean,
  ): Promise<T> {
    const correlationId = requestOptions.correlationId ?? newCorrelationId();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const abortFromCaller = () => controller.abort();
    requestOptions.signal?.addEventListener('abort', abortFromCaller);

    const headers: Record<string, string> = {
      accept: 'application/json',
      [CORRELATION_HEADER]: correlationId,
    };
    const token = options.getToken?.() ?? null;
    if (token) {
      headers.authorization = `Bearer ${token}`;
    }
    if (requestOptions.body !== undefined) {
      headers['content-type'] = 'application/json';
    }

    let response: Response;
    try {
      response = await fetch(buildUrl(baseUrl, path, requestOptions.query), {
        method,
        headers,
        body: requestOptions.body === undefined ? undefined : JSON.stringify(requestOptions.body),
        signal: controller.signal,
        credentials: 'same-origin',
      });
    } catch {
      throw ApiError.network(correlationId);
    } finally {
      clearTimeout(timeout);
      requestOptions.signal?.removeEventListener('abort', abortFromCaller);
    }

    if (response.status === 401 && allowRecovery && options.onUnauthorized) {
      const recovered = await options.onUnauthorized().catch(() => false);
      if (recovered) {
        return execute<T>(method, path, { ...requestOptions, correlationId }, false);
      }
    }

    if (!response.ok) {
      throw await normalizeHttpError(response, correlationId);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    try {
      return (await response.json()) as T;
    } catch {
      throw new ApiError({
        status: response.status,
        code: 'UNKNOWN_ERROR',
        message: 'The service returned an unreadable response.',
        correlationId,
      });
    }
  }

  return {
    request: (method, path, requestOptions = {}) => execute(method, path, requestOptions, true),
    get: (path, requestOptions = {}) => execute('GET', path, requestOptions, true),
    post: (path, body, requestOptions = {}) =>
      execute('POST', path, { ...requestOptions, body }, true),
    patch: (path, body, requestOptions = {}) =>
      execute('PATCH', path, { ...requestOptions, body }, true),
  };
}
