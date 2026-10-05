/** App shell tests (Appendix AL §13, §14, §61). */

import { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { AppShell } from './AppShell';
import { AuthProvider, useAuth } from '../../platform/auth/AuthContext';
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

function makeClient(): { client: ApiClient; post: ReturnType<typeof vi.fn> } {
  const post = vi.fn(async () => ({ token: 'memory-token', user_id: 'user-1' }));
  const get = vi.fn(async () => ME);
  return {
    client: { get, post, patch: vi.fn(), request: vi.fn() } as unknown as ApiClient,
    post,
  };
}

/** Signs in on mount so shell states beyond `unauthenticated` can be asserted. */
function AutoLogin() {
  const { login } = useAuth();
  useEffect(() => {
    void login('ada', 'secret');
  }, [login]);
  return null;
}

function renderShell(client: ApiClient, options: { autoLogin?: boolean } = {}) {
  return render(
    <AuthProvider client={client}>
      {options.autoLogin ? <AutoLogin /> : null}
      <TenantProvider initialTenantId={TENANT}>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<p>shell content</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    </AuthProvider>,
  );
}

describe('AppShell', () => {
  it('renders header, navigation and the main content area', () => {
    const { client } = makeClient();
    renderShell(client);

    expect(screen.getByTestId('uap-app-shell')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByTestId('uap-shell-main')).toHaveTextContent('shell content');
  });

  it('shows the current tenant and, before sign-in, no user', () => {
    const { client } = makeClient();
    renderShell(client);

    expect(screen.getByTestId('uap-shell-tenant')).toHaveTextContent(TENANT);
    expect(screen.getByTestId('uap-shell-user')).toHaveTextContent('not signed in');
    expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument();
  });

  it('shows the signed-in user and signs out through the session endpoint', async () => {
    const { client, post } = makeClient();
    const user = userEvent.setup();
    renderShell(client, { autoLogin: true });

    expect(await screen.findByTestId('uap-shell-user')).toHaveTextContent('user-1');
    await user.click(screen.getByRole('button', { name: 'Sign out' }));

    expect(post).toHaveBeenCalledWith('/sessions/logout', undefined);
  });

  it('carries no Company navigation in the foundation', () => {
    const { client } = makeClient();
    renderShell(client);

    expect(screen.getByRole('navigation', { name: 'Primary' }).textContent).not.toMatch(
      /employee|assignment|company/i,
    );
  });
});
