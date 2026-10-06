/**
 * P21 Company UI surfaces — Reports + AI Copilot (PDL Appendix AP).
 * Real composition (AuthProvider → TenantProvider → module route tree); only the
 * HTTP client is a double.
 */

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { ApiError } from '../../../platform/api';
import { TENANT_A, makeStubClient, renderCompanyModule } from '../../../test/companyHarness';

const REPORT = {
  headcount: 21,
  employee_lifecycle: { active: 14, terminated: 6, suspended: 1 },
  assignment_summary: { active: 14, ended: 5 },
  unassigned_employees: 2,
  space_employee_counts: { 'space-1': 4 },
  space_assignment_counts: { 'space-1': 4 },
};

describe('P21 Company UI surfaces', () => {
  it('renders the six operational report sections', async () => {
    const stub = makeStubClient((call) =>
      call.path.endsWith('/reports/operational') ? REPORT : {},
    );
    renderCompanyModule(stub.client, `/tenants/${TENANT_A}/company/reports`);

    expect(await screen.findByTestId('report-headcount')).toHaveTextContent('21');
    expect(screen.getByTestId('report-lifecycle')).toHaveTextContent('active 14');
    expect(screen.getByTestId('report-assignments')).toHaveTextContent('ended 5');
    expect(screen.getByTestId('report-unassigned')).toHaveTextContent('2');
    expect(screen.getByTestId('report-space-employees')).toHaveTextContent('4');
  });

  it('shows the empty state when the tenant has nothing to report', async () => {
    const stub = makeStubClient(() => ({ ...REPORT, headcount: 0 }));
    renderCompanyModule(stub.client, `/tenants/${TENANT_A}/company/reports`);

    expect(await screen.findByTestId('reports-empty')).toHaveTextContent('还没有可统计');
  });

  it('maps a denied report to customer language without internals', async () => {
    const stub = makeStubClient(
      () => new ApiError({ status: 403, code: 'ACCESS_DENIED', message: 'denied' }),
    );
    renderCompanyModule(stub.client, `/tenants/${TENANT_A}/company/reports`);

    const error = await screen.findByText(/暂时无法读取报表/);
    expect(error).toBeInTheDocument();
    expect(document.body.textContent ?? '').not.toMatch(/sql|constraint|traceback|role_permissions/i);
  });

  it('answers with citations and keeps the proposal ephemeral until confirmed', async () => {
    const user = userEvent.setup();
    const modes: string[] = [];
    const stub = makeStubClient((call) => {
      if (call.path.includes('/assistant/runs')) {
        const body = call.body as { mode: string };
        modes.push(body.mode);
        return {
          status: 'FAILED',
          failure_code: 'CREDENTIAL_UNAVAILABLE',
          mode: body.mode,
          answer: {},
          citations: [{ type: 'company_employee', id: 'emp-1', label: 'Ada Lovelace' }],
          current_state: 'active',
          proposal:
            body.mode === 'propose'
              ? {
                  proposal_id: 'p-1',
                  action: 'company_employee.suspend',
                  resource_type: 'company_employee',
                  resource_id: 'emp-1',
                  expected_state: 'suspended',
                  summary: 'company_employee.suspend → suspended',
                  expires_at: 1,
                }
              : null,
        };
      }
      if (call.path.includes('/proposals/confirm')) {
        return { authorized: true };
      }
      return {};
    });
    renderCompanyModule(stub.client, `/tenants/${TENANT_A}/company/copilot`);

    await user.type(await screen.findByLabelText('你的问题'), '公司有多少员工？');
    await user.click(screen.getByTestId('copilot-ask'));
    expect(await screen.findByTestId('copilot-citation')).toHaveTextContent('Ada Lovelace');

    await user.click(screen.getByTestId('copilot-propose'));
    expect(await screen.findByTestId('copilot-proposal')).toHaveTextContent('suspended');

    // Nothing is executed until the human confirms the proposal.
    await user.click(screen.getByTestId('copilot-confirm'));
    expect(await screen.findByTestId('copilot-confirmed')).toBeInTheDocument();
    expect(modes).toEqual(['answer', 'propose']);
  });
});
