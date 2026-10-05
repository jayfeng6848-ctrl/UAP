/** Company API adapter tests: frozen paths, encoding and query discipline. */

import { describe, expect, it } from 'vitest';

import { makeStubClient, TENANT_A } from '../../test/companyHarness';
import {
  COMPANY_LIST_LIMIT,
  companyPaths,
  createEmployee,
  endAssignment,
  getEmployee,
  listAssignments,
  listEmployees,
  listTenantSpaces,
  suspendEmployee,
  terminateEmployee,
  updateEmployee,
} from './api';

describe('companyPaths', () => {
  it('uses the frozen P20 namespace and encodes identifiers', () => {
    expect(companyPaths.employees('t-1')).toBe('/company/tenants/t-1/employees');
    expect(companyPaths.employee('t-1', 'e/1')).toBe('/company/tenants/t-1/employees/e%2F1');
    expect(companyPaths.suspendEmployee('t-1', 'e 1')).toBe(
      '/company/tenants/t-1/employees/e%201/suspend',
    );
    expect(companyPaths.terminateEmployee('t-1', 'e1')).toBe(
      '/company/tenants/t-1/employees/e1/terminate',
    );
    expect(companyPaths.assignments('t-1')).toBe('/company/tenants/t-1/assignments');
    expect(companyPaths.assignment('t-1', 'a1')).toBe('/company/tenants/t-1/assignments/a1');
    expect(companyPaths.endAssignment('t-1', 'a1')).toBe(
      '/company/tenants/t-1/assignments/a1/end',
    );
    expect(companyPaths.tenantSpaces('t-1')).toBe('/tenants/t-1/spaces');
  });
});

describe('employee calls', () => {
  it('reads the collection with the default page size and no empty filters', async () => {
    const stub = makeStubClient(() => ({ items: [], count: 0, limit: COMPANY_LIST_LIMIT }));

    await listEmployees(stub.client, TENANT_A);

    expect(stub.calls).toHaveLength(1);
    expect(stub.calls[0].method).toBe('GET');
    expect(stub.calls[0].path).toBe(`/company/tenants/${TENANT_A}/employees`);
    expect(stub.calls[0].query).toEqual({ limit: COMPANY_LIST_LIMIT });
  });

  it('passes only the frozen filters that are set', async () => {
    const stub = makeStubClient(() => ({ items: [], count: 0, limit: 5 }));

    await listEmployees(stub.client, TENANT_A, { status: 'suspended', limit: 5 });
    await listAssignments(stub.client, TENANT_A, { employee_id: 'emp-9', limit: 5 });

    expect(stub.calls[0].query).toEqual({ status: 'suspended', limit: 5 });
    expect(stub.calls[1].query).toEqual({ employee_id: 'emp-9', limit: 5 });
  });

  it('sends create/update payloads verbatim', async () => {
    const stub = makeStubClient(() => ({ employee_id: 'e1' }));

    await createEmployee(stub.client, TENANT_A, { employee_no: 'E-1', display_name: 'Ada' });
    await updateEmployee(stub.client, TENANT_A, 'e1', { title: 'Lead' });

    expect(stub.calls[0]).toMatchObject({
      method: 'POST',
      path: `/company/tenants/${TENANT_A}/employees`,
      body: { employee_no: 'E-1', display_name: 'Ada' },
    });
    expect(stub.calls[1]).toMatchObject({
      method: 'PATCH',
      path: `/company/tenants/${TENANT_A}/employees/e1`,
      body: { title: 'Lead' },
    });
  });

  it('reads one employee and sends lifecycle actions without a body', async () => {
    const stub = makeStubClient(() => ({ employee_id: 'e1' }));

    await getEmployee(stub.client, TENANT_A, 'e1');
    await suspendEmployee(stub.client, TENANT_A, 'e1');
    await terminateEmployee(stub.client, TENANT_A, 'e1');
    await endAssignment(stub.client, TENANT_A, 'a1');
    await listTenantSpaces(stub.client, TENANT_A);

    expect(stub.calls.map((call) => [call.method, call.path])).toEqual([
      ['GET', `/company/tenants/${TENANT_A}/employees/e1`],
      ['POST', `/company/tenants/${TENANT_A}/employees/e1/suspend`],
      ['POST', `/company/tenants/${TENANT_A}/employees/e1/terminate`],
      ['POST', `/company/tenants/${TENANT_A}/assignments/a1/end`],
      ['GET', `/tenants/${TENANT_A}/spaces`],
    ]);
    expect(stub.calls.every((call) => call.body === undefined)).toBe(true);
  });
});
