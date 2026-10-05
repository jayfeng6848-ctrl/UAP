/** Company overview: per-resource loading, empty, error and populated states. */

import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ApiError } from '../../platform/api';
import {
  TENANT_A,
  assignmentFixture,
  employeeFixture,
  makeStubClient,
  renderCompanyModule,
} from '../../test/companyHarness';
import type { RecordedCall } from '../../test/companyHarness';

const entry = `/tenants/${TENANT_A}/company`;

function overviewHandler(call: RecordedCall) {
  if (call.path.endsWith('/assignments')) {
    return { items: [assignmentFixture()], count: 1, limit: 5 };
  }
  return { items: [employeeFixture()], count: 1, limit: 5 };
}

describe('OverviewPage', () => {
  it('renders both recent slices with links into the module', async () => {
    const stub = makeStubClient(overviewHandler);
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-overview')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Company overview' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ada Lovelace' })).toHaveAttribute(
      'href',
      `/tenants/${TENANT_A}/company/employees/emp-1`,
    );
    expect(screen.getByRole('link', { name: 'member' })).toHaveAttribute(
      'href',
      `/tenants/${TENANT_A}/company/assignments/asg-1`,
    );
    expect(screen.getByRole('link', { name: 'View all employees' })).toHaveAttribute(
      'href',
      `/tenants/${TENANT_A}/company/employees`,
    );
    const limits = screen.getAllByText(/Showing 1 of at most 5 records\./);
    expect(limits).toHaveLength(2);
    // Both reads are tenant-scoped and limited (no unbounded scan).
    expect(stub.calls.map((call) => call.query)).toEqual([
      { limit: 5 },
      { limit: 5 },
    ]);
  });

  it('shows an empty state per area when the tenant has no records', async () => {
    const stub = makeStubClient(() => ({ items: [], count: 0, limit: 5 }));
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByText('No employees yet')).toBeInTheDocument();
    expect(screen.getByText('No assignments yet')).toBeInTheDocument();
  });

  it('keeps one failed area from hiding the other (per-resource error state)', async () => {
    const stub = makeStubClient((call) => {
      if (call.path.endsWith('/employees')) {
        return new ApiError({ status: 403, code: 'ACCESS_DENIED', message: 'denied' });
      }
      return { items: [assignmentFixture()], count: 1, limit: 5 };
    });
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-error')).toHaveTextContent(
      'You do not have access to this resource.',
    );
    expect(screen.getByRole('link', { name: 'member' })).toBeInTheDocument();
  });
});
