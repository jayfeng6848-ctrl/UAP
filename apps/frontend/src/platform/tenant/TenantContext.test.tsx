/**
 * Tenant context tests (Appendix AL §16-§18, §54).
 *
 * URL tenant → context tenant. The context is *not* an authorization credential:
 * an unreachable tenant is refused by the backend (403), never by the frontend.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { TenantProvider, isValidTenantId, useTenant } from './TenantContext';
import { TenantBoundary } from '../../app/routing/TenantBoundary';

const TENANT_A = '3f1a2b4c-5d6e-4f70-8192-a3b4c5d6e7f8';
const TENANT_B = '00000000-0000-4000-8000-000000000001';

function TenantProbe() {
  const { tenantId } = useTenant();
  return <span data-testid="probe-tenant">{tenantId ?? 'none'}</span>;
}

/** Sibling probe: proves the boundary owns the *shared* context value. */
function OutsideTenantProbe() {
  const { tenantId } = useTenant();
  return <span data-testid="outside-tenant">{tenantId ?? 'none'}</span>;
}

function TenantScreen({ initialEntry }: { initialEntry: string }) {
  return (
    <TenantProvider>
      <OutsideTenantProbe />
      <MemoryRouter initialEntries={[initialEntry]}>
        <nav>
          <Link to={`/tenants/${TENANT_A}/company`}>tenant A</Link>
          <Link to={`/tenants/${TENANT_B}/company`}>tenant B</Link>
        </nav>
        <Routes>
          <Route path="/home" element={<span>home</span>} />
          <Route
            path="/tenants/:tenant_id/company"
            element={
              <>
                <TenantBoundary>
                  <TenantProbe />
                </TenantBoundary>
                <Link to="/home">leave tenant view</Link>
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    </TenantProvider>
  );
}

describe('isValidTenantId', () => {
  it('accepts a canonical uuid and rejects anything else', () => {
    expect(isValidTenantId(TENANT_A)).toBe(true);
    expect(isValidTenantId(TENANT_A.toUpperCase())).toBe(true);
    expect(isValidTenantId('not-a-uuid')).toBe(false);
    expect(isValidTenantId('123')).toBe(false);
    expect(isValidTenantId('')).toBe(false);
    expect(isValidTenantId(undefined)).toBe(false);
    expect(isValidTenantId(null)).toBe(false);
  });
});

describe('TenantProvider', () => {
  it('starts unresolved', () => {
    render(
      <TenantProvider>
        <TenantProbe />
      </TenantProvider>,
    );

    expect(screen.getByTestId('probe-tenant')).toHaveTextContent('none');
  });

  it('throws when useTenant is used outside the provider', () => {
    expect(() => render(<TenantProbe />)).toThrowError(/TenantProvider/);
  });
});

describe('TenantBoundary', () => {
  it('mirrors a valid URL tenant into the shared context', () => {
    render(<TenantScreen initialEntry={`/tenants/${TENANT_A}/company`} />);

    expect(screen.getByTestId('probe-tenant')).toHaveTextContent(TENANT_A);
    expect(screen.getAllByTestId('outside-tenant')[0]).toHaveTextContent(TENANT_A);
    expect(screen.queryByTestId('uap-tenant-unresolved')).not.toBeInTheDocument();
  });

  it('updates the shared context when the URL tenant changes', async () => {
    const user = userEvent.setup();
    render(<TenantScreen initialEntry={`/tenants/${TENANT_A}/company`} />);
    expect(screen.getByTestId('probe-tenant')).toHaveTextContent(TENANT_A);

    await user.click(screen.getByRole('link', { name: 'tenant B' }));

    expect(screen.getByTestId('probe-tenant')).toHaveTextContent(TENANT_B);
    expect(screen.getAllByTestId('outside-tenant')[0]).toHaveTextContent(TENANT_B);
  });

  it('blocks an invalid identifier and keeps the context empty', () => {
    render(<TenantScreen initialEntry="/tenants/not-a-tenant/company" />);

    expect(screen.getByTestId('uap-tenant-unresolved')).toHaveTextContent(
      'Tenant context unavailable',
    );
    expect(screen.queryByTestId('probe-tenant')).not.toBeInTheDocument();
    expect(screen.getAllByTestId('outside-tenant')[0]).toHaveTextContent('none');
  });

  it('clears the shared context when the boundary unmounts', async () => {
    const user = userEvent.setup();
    render(<TenantScreen initialEntry={`/tenants/${TENANT_A}/company`} />);
    expect(screen.getByTestId('probe-tenant')).toHaveTextContent(TENANT_A);

    await user.click(screen.getByRole('link', { name: 'leave tenant view' }));

    expect(screen.queryByTestId('probe-tenant')).not.toBeInTheDocument();
    expect(screen.getAllByTestId('outside-tenant')[0]).toHaveTextContent('none');
  });
});
