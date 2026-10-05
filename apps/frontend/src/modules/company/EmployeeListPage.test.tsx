/** Employee collection: real states, frozen filters and the create action. */

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
import type { RecordedCall } from '../../test/companyHarness';

const LIST_PATH = `/company/tenants/${TENANT_A}/employees`;
const entry = `/tenants/${TENANT_A}/company/employees`;

const listOf = (items: unknown[]) => ({ items, count: items.length, limit: 25 });

describe('EmployeeListPage', () => {
  it('shows a loading state while the collection is pending', async () => {
    const stub = makeStubClient(() => new Promise(() => undefined));
    renderCompanyModule(stub.client, entry);

    await waitFor(() =>
      expect(screen.getByTestId('uap-loading-state')).toHaveTextContent('Loading employees…'),
    );
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('renders the employee rows with links and status text', async () => {
    const stub = makeStubClient(() => listOf([employeeFixture()]));
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
    expect(screen.getByText('E-001')).toBeInTheDocument();
    expect(screen.getAllByText('active').length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: 'Open' })).toHaveAttribute(
      'href',
      `/tenants/${TENANT_A}/company/employees/emp-1`,
    );
  });

  it('shows the empty state when the tenant has no employees', async () => {
    const stub = makeStubClient(() => listOf([]));
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-empty')).toHaveTextContent('No employees');
  });

  it('maps a 403 to the no-access message without leaking internals', async () => {
    const stub = makeStubClient(
      () => new ApiError({ status: 403, code: 'ACCESS_DENIED', message: 'denied', correlationId: 'c1' }),
    );
    renderCompanyModule(stub.client, entry);

    const error = await screen.findByTestId('company-error');
    expect(error).toHaveTextContent('You do not have access to this resource.');
    expect(error).toHaveTextContent('c1');
    expect(error.textContent).not.toMatch(/sql|constraint|traceback/i);
  });

  it('surfaces a 401 (session no longer recoverable) as an authentication message', async () => {
    const stub = makeStubClient(
      () => new ApiError({ status: 401, code: 'AUTH_REQUIRED', message: 'auth required' }),
    );
    renderCompanyModule(stub.client, entry);

    expect(await screen.findByTestId('company-error')).toHaveTextContent(
      'Your session has ended. Please sign in again.',
    );
  });

  it('creates an employee through the frozen endpoint and reloads the list', async () => {
    const user = userEvent.setup();
    const created: RecordedCall[] = [];
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        created.push(call);
        return employeeFixture({ employee_id: 'emp-2', display_name: 'Grace Hopper' });
      }
      return listOf([employeeFixture()]);
    });
    renderCompanyModule(stub.client, entry);
    await screen.findByText('Ada Lovelace');

    await user.click(screen.getByTestId('new-employee'));
    await user.type(screen.getByLabelText('Employee number'), 'E-002');
    await user.type(screen.getByLabelText('Display name'), 'Grace Hopper');
    await user.type(screen.getByLabelText('Title (optional)'), 'Rear Admiral');
    await user.click(screen.getByTestId('employee-submit'));

    await waitFor(() => expect(created).toHaveLength(1));
    expect(created[0].path).toBe(LIST_PATH);
    expect(created[0].body).toEqual({
      employee_no: 'E-002',
      display_name: 'Grace Hopper',
      title: 'Rear Admiral',
    });
    expect(await screen.findByText('Employee created.')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    await waitFor(() =>
      expect(stub.callsTo('GET', '/employees').length).toBeGreaterThanOrEqual(2),
    );
  });

  it('keeps the dialog open and shows the conflict message on 409', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        return new ApiError({ status: 409, code: 'CONFLICT', message: 'conflict' });
      }
      return listOf([employeeFixture()]);
    });
    renderCompanyModule(stub.client, entry);
    await screen.findByText('Ada Lovelace');

    await user.click(screen.getByTestId('new-employee'));
    await user.type(screen.getByLabelText('Employee number'), 'E-001');
    await user.type(screen.getByLabelText('Display name'), 'Duplicate');
    await user.click(screen.getByTestId('employee-submit'));

    expect(
      await screen.findByText('This change conflicts with the current state. Reload and try again.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByText('Employee created.')).not.toBeInTheDocument();
  });

  it('blocks an invalid employee number before calling the API', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient(() => listOf([]));
    renderCompanyModule(stub.client, entry);
    await screen.findByTestId('company-empty');

    await user.click(screen.getByTestId('new-employee'));
    await user.type(screen.getByLabelText('Employee number'), 'bad no!');
    await user.type(screen.getByLabelText('Display name'), 'Ada');
    await user.click(screen.getByTestId('employee-submit'));

    expect(
      screen.getByText('Use 1–64 letters, digits, dot, dash or underscore.'),
    ).toBeInTheDocument();
    expect(stub.callsTo('POST', '/employees')).toHaveLength(0);
  });

  it('refetches with the selected status filter', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient(() => listOf([employeeFixture()]));
    renderCompanyModule(stub.client, entry);
    await screen.findByText('Ada Lovelace');

    await user.selectOptions(screen.getByLabelText('Status'), 'suspended');

    await waitFor(() => {
      const calls = stub.callsTo('GET', '/employees');
      expect(calls.at(-1)?.query).toEqual({ status: 'suspended', limit: 25 });
    });
  });
});
