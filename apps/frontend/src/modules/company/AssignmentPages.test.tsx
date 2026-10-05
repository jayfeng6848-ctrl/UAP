/** Assignment collection and detail: enrichment, create, role edit and end. */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import {
  TENANT_A,
  assignmentFixture,
  employeeFixture,
  makeStubClient,
  renderCompanyModule,
} from '../../test/companyHarness';
import type { RecordedCall } from '../../test/companyHarness';

const listPath = `/company/tenants/${TENANT_A}/assignments`;
const listEntry = `/tenants/${TENANT_A}/company/assignments`;
const detailEntry = `/tenants/${TENANT_A}/company/assignments/asg-1`;

const spaceFixture = {
  id: 'space-1',
  tenant_id: TENANT_A,
  key: 'eng',
  name: 'Engineering',
  kind: 'team',
  visibility: 'tenant',
  status: 'active',
};

function handlerWithOptions(overrides: { spaces?: unknown[] } = {}) {
  return (call: RecordedCall) => {
    if (call.path === listPath) {
      return { items: [assignmentFixture()], count: 1, limit: 25 };
    }
    if (call.path.endsWith('/employees')) {
      return { items: [employeeFixture()], count: 1, limit: 100 };
    }
    if (call.path.endsWith('/spaces')) {
      const items = overrides.spaces ?? [spaceFixture];
      return { items, count: items.length };
    }
    return assignmentFixture();
  };
}

describe('AssignmentListPage', () => {
  it('renders assignments enriched with real employee and space names', async () => {
    const stub = makeStubClient(handlerWithOptions());
    renderCompanyModule(stub.client, listEntry);

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getAllByText('member').length).toBeGreaterThan(0);
    // Real options are read from the backend, not from a hard-coded tree.
    expect(stub.callsTo('GET', '/employees').length).toBeGreaterThan(0);
    expect(stub.callsTo('GET', `/tenants/${TENANT_A}/spaces`).length).toBeGreaterThan(0);
  });

  it('creates an assignment from backend-provided employee and space options', async () => {
    const user = userEvent.setup();
    const posts: RecordedCall[] = [];
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        posts.push(call);
        return assignmentFixture();
      }
      return handlerWithOptions()(call);
    });
    renderCompanyModule(stub.client, listEntry);
    await screen.findByText('Engineering');

    await user.click(screen.getByTestId('new-assignment'));
    await user.selectOptions(screen.getByLabelText('Employee'), 'emp-1');
    await user.selectOptions(screen.getByLabelText('Space'), 'space-1');
    await user.click(screen.getByTestId('assignment-submit'));

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0].path).toBe(listPath);
    expect(posts[0].body).toEqual({
      employee_id: 'emp-1',
      space_id: 'space-1',
      assignment_role: 'member',
    });
    expect(await screen.findByText('Assignment created.')).toBeInTheDocument();
  });

  it('explains when no active space is available', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient(handlerWithOptions({ spaces: [] }));
    renderCompanyModule(stub.client, listEntry);
    await screen.findByText('Ada Lovelace');

    await user.click(screen.getByTestId('new-assignment'));

    expect(screen.getByTestId('assignment-no-spaces')).toHaveTextContent(
      'No active space is available to assign work to.',
    );
  });
});

describe('AssignmentDetailPage', () => {
  it('edits the assignment role through PATCH', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient(() => assignmentFixture({ assignment_role: 'lead' }));
    renderCompanyModule(stub.client, detailEntry);
    await screen.findByTestId('company-assignment-detail');

    await user.click(screen.getByTestId('edit-assignment'));
    await user.selectOptions(screen.getByLabelText('Assignment role'), 'lead');
    await user.click(screen.getByTestId('assignment-submit'));

    await waitFor(() =>
      expect(stub.callsTo('PATCH', `/assignments/asg-1`)).toHaveLength(1),
    );
    expect(stub.callsTo('PATCH', '/assignments/asg-1')[0].body).toEqual({
      assignment_role: 'lead',
    });
    expect(await screen.findByText('Assignment updated.')).toBeInTheDocument();
  });

  it('ends the assignment only after confirmation', async () => {
    const user = userEvent.setup();
    const stub = makeStubClient((call) => {
      if (call.method === 'POST') {
        return assignmentFixture({ status: 'ended' });
      }
      return assignmentFixture();
    });
    renderCompanyModule(stub.client, detailEntry);
    await screen.findByTestId('company-assignment-detail');

    await user.click(screen.getByTestId('end-assignment'));
    expect(stub.callsTo('POST', '/end')).toHaveLength(0);

    await user.click(screen.getByTestId('confirm-action'));

    await waitFor(() => expect(stub.callsTo('POST', '/end')).toHaveLength(1));
    expect(await screen.findByText('Assignment ended.')).toBeInTheDocument();
  });

  it('disables edit and end for a terminal assignment', async () => {
    const stub = makeStubClient(() => assignmentFixture({ status: 'ended' }));
    renderCompanyModule(stub.client, detailEntry);
    await screen.findByTestId('company-assignment-detail');

    expect(screen.getByTestId('edit-assignment')).toBeDisabled();
    expect(screen.getByTestId('end-assignment')).toBeDisabled();
  });
});
