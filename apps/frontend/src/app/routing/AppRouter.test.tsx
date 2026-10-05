/**
 * Routing tests (Appendix AL §15-§18, §42, §54 · HD-P21-01).
 *
 * The Company route now mounts the implemented module tree inside the platform
 * auth + tenant boundaries; API access is stubbed here (real backend integration
 * is covered by the module's own tests and by the live verification run).
 */

import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { AppRouter } from './AppRouter';
import { AuthProvider, useAuth } from '../../platform/auth/AuthContext';
import { FeedbackProvider } from '../../platform/feedback/FeedbackProvider';
import { TenantProvider } from '../../platform/tenant/TenantContext';
import type { ApiClient, MeResponse } from '../../platform/api';

const TENANT = '3f1a2b4c-5d6e-4f70-8192-a3b4c5d6e7f8';

const ME: MeResponse = {
  correlation_id: 'corr',
  session_id: 'sess-1',
  device_id: 'dev-1',
  identity_id: 'ident-1',
  user_id: 'user-1',
  tenant_id: TENANT,
  space_id: null,
  subject_type: 'user',
  scope: null,
  authentication_assurance: 'verified_device',
};

/** Path-aware stub: `/me`, `/sessions` and empty Company/P17 collections. */
function makeClient(): ApiClient {
  const post = vi.fn(async () => ({ token: 'memory-token', user_id: 'user-1' }));
  const get = vi.fn(async (path: string) => {
    if (path === '/me') {
      return ME;
    }
    if (path.endsWith('/spaces')) {
      return { items: [], count: 0 };
    }
    return { items: [], count: 0, limit: 25 };
  });
  return { get, post, patch: vi.fn(), request: vi.fn() } as unknown as ApiClient;
}

function AutoLogin() {
  const { login } = useAuth();
  useEffect(() => {
    void login('ada', 'secret');
  }, [login]);
  return null;
}

/**
 * The router only mounts once the session exists — mirroring a reload of an
 * already-signed-in console (the memory token lives in the provider).
 */
function AuthenticatedApp({ entry, children }: { entry: string; children: ReactNode }) {
  const { status } = useAuth();
  if (status === 'authenticated') {
    return <MemoryRouter initialEntries={[entry]}>{children}</MemoryRouter>;
  }
  return <p data-testid="uap-auth-pending">{status}</p>;
}

function renderRoute(entry: string, options: { autoLogin?: boolean } = {}) {
  return render(
    <FeedbackProvider>
      <AuthProvider client={makeClient()}>
        {options.autoLogin ? <AutoLogin /> : null}
        <TenantProvider>
          {options.autoLogin ? (
            <AuthenticatedApp entry={entry}>
              <AppRouter />
            </AuthenticatedApp>
          ) : (
            <MemoryRouter initialEntries={[entry]}>
              <AppRouter />
            </MemoryRouter>
          )}
        </TenantProvider>
      </AuthProvider>
    </FeedbackProvider>,
  );
}

describe('AppRouter', () => {
  it('sends an unauthenticated visitor to the sign-in page', async () => {
    renderRoute('/');

    expect(await screen.findByRole('heading', { name: 'Sign in to UAP Console' })).toBeInTheDocument();
  });

  it('renders the platform home once authenticated', async () => {
    renderRoute('/', { autoLogin: true });

    expect(await screen.findByTestId('uap-home-user')).toHaveTextContent('user-1');
    expect(screen.getByTestId('uap-home-company-status')).toHaveTextContent('IMPLEMENTED');
  });

  it('renders the Company overview for the URL tenant', async () => {
    renderRoute(`/tenants/${TENANT}/company`, { autoLogin: true });

    expect(await screen.findByTestId('company-overview')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Company overview' })).toBeInTheDocument();
    expect(screen.getByTestId('uap-shell-tenant')).toHaveTextContent(TENANT);
    expect(screen.getByRole('navigation', { name: 'Company' })).toBeInTheDocument();
  });

  it('renders the Company employee collection route', async () => {
    renderRoute(`/tenants/${TENANT}/company/employees`, { autoLogin: true });

    expect(await screen.findByTestId('company-employees')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Employees' })).toBeInTheDocument();
  });

  it('answers an unknown Company sub-path with the module 404', async () => {
    renderRoute(`/tenants/${TENANT}/company/nope`, { autoLogin: true });

    expect(await screen.findByRole('heading', { name: 'Company page not found' })).toBeInTheDocument();
  });

  it('refuses an invalid tenant identifier', async () => {
    renderRoute('/tenants/not-a-tenant/company', { autoLogin: true });

    expect(await screen.findByTestId('uap-tenant-unresolved')).toBeInTheDocument();
    expect(screen.queryByTestId('company-overview')).not.toBeInTheDocument();
  });

  it('serves the 403 and not-found routes', async () => {
    renderRoute('/403');
    expect(await screen.findByRole('heading', { name: 'Access denied' })).toBeInTheDocument();

    renderRoute('/does-not-exist');
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument();
  });
});
