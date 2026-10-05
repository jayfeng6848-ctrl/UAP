/**
 * Company module test harness (test-only; not imported by application code).
 *
 * Mounts the real module route tree inside the real platform providers and the
 * real tenant boundary, so tests exercise the production composition:
 * AuthProvider (injected client) → TenantProvider → route → TenantBoundary → module.
 */

import type { ReactNode } from 'react';
import { render } from '@testing-library/react';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';

import { CompanyRouteTree } from '../modules/company';
import { AuthProvider } from '../platform/auth/AuthContext';
import { FeedbackProvider } from '../platform/feedback/FeedbackProvider';
import { TenantProvider } from '../platform/tenant/TenantContext';
import { TenantBoundary } from '../app/routing/TenantBoundary';
import type { ApiClient } from '../platform/api';

export const TENANT_A = '3f1a2b4c-5d6e-4f70-8192-a3b4c5d6e7f8';
export const TENANT_B = '00000000-0000-4000-8000-000000000001';

export interface RecordedCall {
  method: string;
  path: string;
  body?: unknown;
  query?: Record<string, string | number>;
}

export interface StubController {
  client: ApiClient;
  calls: RecordedCall[];
  callsTo(method: string, pathSuffix: string): RecordedCall[];
}

/**
 * Deterministic API client double: `handler` returns the payload or throws an
 * `ApiError` to simulate a backend failure. Every call is recorded for assertions.
 */
export function makeStubClient(handler: (call: RecordedCall) => unknown): StubController {
  const calls: RecordedCall[] = [];
  const run = async (
    method: string,
    path: string,
    body?: unknown,
    options?: { query?: Record<string, string | number> },
  ): Promise<unknown> => {
    const call: RecordedCall = { method, path, body, query: options?.query };
    calls.push(call);
    const result = handler(call);
    if (result instanceof Error) {
      throw result;
    }
    return result;
  };

  const client = {
    get: (path: string, options?: { query?: Record<string, string | number> }) =>
      run('GET', path, undefined, options),
    post: (path: string, body?: unknown, options?: { query?: Record<string, string | number> }) =>
      run('POST', path, body, options),
    patch: (path: string, body?: unknown, options?: { query?: Record<string, string | number> }) =>
      run('PATCH', path, body, options),
    request: (method: string, path: string, options?: { query?: Record<string, string | number> }) =>
      run(method, path, undefined, options),
  } as unknown as ApiClient;

  return {
    client,
    calls,
    callsTo: (method: string, pathSuffix: string) =>
      calls.filter((call) => call.method === method && call.path.endsWith(pathSuffix)),
  };
}

/** Tenant switch affordance used by the tenant-boundary tests. */
export function TenantSwitcher() {
  return (
    <div>
      <Link to={`/tenants/${TENANT_A}/company/employees`}>switch to A</Link>
      <Link to={`/tenants/${TENANT_B}/company/employees`}>switch to B</Link>
    </div>
  );
}

export function renderCompanyModule(
  client: ApiClient,
  entry: string,
  options: { withSwitcher?: boolean } = {},
): ReturnType<typeof render> {
  const switcher: ReactNode = options.withSwitcher ? <TenantSwitcher /> : null;
  return render(
    <FeedbackProvider>
      <AuthProvider client={client}>
        <TenantProvider>
          <MemoryRouter initialEntries={[entry]}>
            {switcher}
            <Routes>
              <Route
                path="/tenants/:tenant_id/company/*"
                element={
                  <TenantBoundary>
                    <CompanyRouteTree />
                  </TenantBoundary>
                }
              />
            </Routes>
          </MemoryRouter>
        </TenantProvider>
      </AuthProvider>
    </FeedbackProvider>,
  );
}

/**
 * Renders the module *without* the tenant boundary and with a deliberately stale
 * context tenant — the exact condition the guard must refuse to act on.
 */
export function renderCompanyModuleWithStaleContext(
  client: ApiClient,
  entry: string,
  contextTenantId: string,
): ReturnType<typeof render> {
  return render(
    <FeedbackProvider>
      <AuthProvider client={client}>
        <TenantProvider initialTenantId={contextTenantId}>
          <MemoryRouter initialEntries={[entry]}>
            <Routes>
              <Route path="/tenants/:tenant_id/company/*" element={<CompanyRouteTree />} />
            </Routes>
          </MemoryRouter>
        </TenantProvider>
      </AuthProvider>
    </FeedbackProvider>,
  );
}

/** Fixture helpers shared by the module tests. */
export function employeeFixture(overrides: Record<string, unknown> = {}) {
  return {
    employee_id: 'emp-1',
    tenant_id: TENANT_A,
    employee_no: 'E-001',
    display_name: 'Ada Lovelace',
    title: 'Engineer',
    status: 'active',
    user_id: null,
    hired_at: null,
    terminated_at: null,
    created_at: '2026-10-01T08:00:00+00:00',
    updated_at: '2026-10-01T08:00:00+00:00',
    ...overrides,
  };
}

export function assignmentFixture(overrides: Record<string, unknown> = {}) {
  return {
    assignment_id: 'asg-1',
    tenant_id: TENANT_A,
    employee_id: 'emp-1',
    space_id: 'space-1',
    assignment_role: 'member',
    status: 'active',
    started_at: '2026-10-01T08:00:00+00:00',
    ended_at: null,
    created_at: '2026-10-01T08:00:00+00:00',
    updated_at: '2026-10-01T08:00:00+00:00',
    ...overrides,
  };
}
