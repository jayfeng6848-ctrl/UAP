/** Employee detail: profile, edit and the confirmed lifecycle actions. */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { ApiError } from '../../platform/api';
import {
  TENANT_A,
  employeeFixture,
  makeStubClient,
  renderCompanyModule,
} from '../../test/companyHarness';

const base = `/company/tenants/${TENANT_A}/employees`;
const entry = `/tenants/${TENANT_A}/company/employees/emp-1`;
const emptyAssignments = { items: [], count: 0, limit: 10 };

describe('EmployeeDetailPage', () => {
  it('renders the profile and the employee assignments section', async () => {
    const stub = makeStubClient((call) =>
      call.path === `${base}/emp-1` ? employeeFixture() : emptyAssignments,
    );
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-employee-detail')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Ada Lovelace' })).toBeInTheDocument();
    expect(screen.getByText('E-001')).toBeInTheDocument();
    expect(screen.getByText('Engineer')).toBeInTheDocument();
    expect(screen.getByText(/binding is a separate authorized action/)).toBeInTheDocument();
    expect(screen.getByTestId('company-empty')).toHaveTextContent('No assignments');
  });

  it('requires confirmation before suspending, then reloads the employee', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        return employeeFixture({ status: 'suspended' });
      }
      return call.path === `${base}/emp-1` ? employeeFixture() : emptyAssignments;
    });
    renderCompanyModule(stub.client, entry);
    await screen.findByTestId('company-employee-detail');

    await user.click(screen.getByTestId('suspend-employee'));
    expect(screen.getByRole('dialog')).toHaveTextContent('Suspend employee');
    expect(stub.callsTo('POST', '/suspend')).toHaveLength(0);

    await user.click(screen.getByTestId('confirm-action'));

    await waitFor(() => expect(stub.callsTo('POST', '/suspend')).toHaveLength(1));
    expect(await screen.findByText('Employee suspended.')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('maps a lifecycle 409 into the confirmation dialog and keeps it open', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        return new ApiError({ status: 409, code: 'CONFLICT', message: 'conflict' });
      }
      return call.path === `${base}/emp-1` ? employeeFixture() : emptyAssignments;
    });
    renderCompanyModule(stub.client, entry);
    await screen.findByTestId('company-employee-detail');

    await user.click(screen.getByTestId('terminate-employee'));
    await user.click(screen.getByTestId('confirm-action'));

    expect(
      await screen.findByText('This change conflicts with the current state. Reload and try again.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByText('Employee terminated.')).not.toBeInTheDocument();
  });

  it('disables lifecycle actions that the frozen lifecycle does not allow', async () => {
    const stub = makeStubClient((call) =>
      call.path === `${base}/emp-1` ? employeeFixture({ status: 'terminated' }) : emptyAssignments,
    );
    renderCompanyModule(stub.client, entry);
    await screen.findByTestId('company-employee-detail');

    expect(screen.getByTestId('suspend-employee')).toBeDisabled();
    expect(screen.getByTestId('terminate-employee')).toBeDisabled();
  });

  it('edits only the changed fields through PATCH', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => {
      if (call.method === 'PATCH') {
        return employeeFixture({ title: 'Lead' });
      }
      return call.path === `${base}/emp-1` ? employeeFixture() : emptyAssignments;
    });
    renderCompanyModule(stub.client, entry);
    await screen.findByTestId('company-employee-detail');

    await user.click(screen.getByTestId('edit-employee'));
    await user.clear(screen.getByLabelText('Title (optional)'));
    await user.type(screen.getByLabelText('Title (optional)'), 'Lead');
    await user.click(screen.getByTestId('employee-submit'));

    await waitFor(() => expect(stub.callsTo('PATCH', '/employees/emp-1')).toHaveLength(1));
    expect(stub.callsTo('PATCH', '/employees/emp-1')[0].body).toEqual({ title: 'Lead' });
    expect(await screen.findByText('Employee updated.')).toBeInTheDocument();
  });

  it('shows the not-found/validation message when the employee cannot be read', async () => {
    const stub = makeStubClient(
      () =>
        new ApiError({ status: 422, code: 'VALIDATION_OR_NOT_FOUND', message: 'not found' }),
    );
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-error')).toHaveTextContent(
      'The request could not be processed. Check the values and try again.',
    );
  });
});
