/**
 * Tenant correctness constraint for Company UI (HD-P21-01 · F-P21-RE-01).
 *
 * The URL is the tenant authority. While the platform context has not caught up,
 * the module renders a resolving state and issues no request; a tenant switch
 * never issues a request for the previous tenant and never renders its data
 * under the new tenant.
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import {
  TENANT_A,
  TENANT_B,
  employeeFixture,
  makeStubClient,
  renderCompanyModule,
  renderCompanyModuleWithStaleContext,
} from '../../test/companyHarness';

function tenantNamedList(path: string) {
  const tenant = path.includes(TENANT_B) ? TENANT_B : TENANT_A;
  const label = tenant === TENANT_A ? 'Employee A' : 'Employee B';
  return {
    items: [employeeFixture({ tenant_id: tenant, employee_id: `emp-${label}`, display_name: label })],
    count: 1,
    limit: 25,
  };
}

describe('Company tenant guard', () => {
  it('does not call the API for a tenant that the context has not confirmed', () => {
    const stub = makeStubClient((call) => tenantNamedList(call.path));

    // URL says tenant A while the platform context still holds tenant B.
    renderCompanyModuleWithStaleContext(
      stub.client,
      `/tenants/${TENANT_A}/company/employees`,
      TENANT_B,
    );

    expect(screen.getByTestId('company-tenant-resolving')).toBeInTheDocument();
    expect(screen.queryByTestId('company-employees')).not.toBeInTheDocument();
    expect(stub.calls).toHaveLength(0);
  });

  it('switches tenants as a whole: new requests target B and A data is gone', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => tenantNamedList(call.path));

    renderCompanyModule(stub.client, `/tenants/${TENANT_A}/company/employees`, {
      withSwitcher: true,
    });
    await screen.findByText('Employee A');

    const callsBefore = stub.calls.length;
    await user.click(screen.getByRole('link', { name: 'switch to B' }));
    await screen.findByText('Employee B');

    const callsAfter = stub.calls.slice(callsBefore);
    expect(callsAfter.length).toBeGreaterThan(0);
    expect(callsAfter.every((call) => call.path.includes(TENANT_B))).toBe(true);
    expect(callsAfter.some((call) => call.path.includes(TENANT_A))).toBe(false);
    await waitFor(() => expect(screen.queryByText('Employee A')).not.toBeInTheDocument());
  });

  it('renders nothing company-specific for an invalid tenant identifier', () => {
    const stub = makeStubClient(() => ({ items: [], count: 0, limit: 25 }));

    renderCompanyModule(stub.client, '/tenants/not-a-tenant/company/employees');

    expect(screen.getByTestId('uap-tenant-unresolved')).toBeInTheDocument();
    expect(screen.queryByTestId('company-employees')).not.toBeInTheDocument();
    expect(stub.calls).toHaveLength(0);
  });
});
