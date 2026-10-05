/**
 * Company API adapter (HD-P21-01 · PDL Appendix AG).
 *
 * The only place that knows Company URL paths and DTO shapes. It never builds its
 * own HTTP client: every call goes through the platform's typed API client, so
 * correlation headers, timeout/abort, the memory-only session token, 401 recovery
 * and the frozen error taxonomy are reused instead of duplicated.
 *
 * Frozen endpoints (11, exactly the accepted P20 set — no endpoint was added):
 *   POST/GET   /company/tenants/{tenant_id}/employees
 *   GET/PATCH  /company/tenants/{tenant_id}/employees/{employee_id}
 *   POST       /company/tenants/{tenant_id}/employees/{employee_id}/suspend|terminate
 *   POST/GET   /company/tenants/{tenant_id}/assignments
 *   GET/PATCH  /company/tenants/{tenant_id}/assignments/{assignment_id}
 *   POST       /company/tenants/{tenant_id}/assignments/{assignment_id}/end
 *
 * The assignment space picker reads the P17 structure namespace
 * (`GET /tenants/{tenant_id}/spaces`) — legitimate backend data, never a
 * hard-coded organisation tree (Appendix AL.6).
 */

import type { ApiClient } from '../../platform/api';

/** Default page size used by Company list views (the API accepts 1…200). */
export const COMPANY_LIST_LIMIT = 25;

// ------------------------------------------------------------------ contracts
export interface Employee {
  employee_id: string;
  tenant_id: string;
  employee_no: string;
  display_name: string;
  title: string | null;
  status: string;
  user_id: string | null;
  hired_at: string | null;
  terminated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Assignment {
  assignment_id: string;
  tenant_id: string;
  employee_id: string;
  space_id: string;
  assignment_role: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/** `GET /tenants/{tenant_id}/spaces` row (P17 structure read). */
export interface TenantSpace {
  id: string;
  tenant_id: string;
  key: string;
  name: string;
  kind: string;
  visibility: string;
  status: string;
}

export interface ListEnvelope<T> {
  items: T[];
  count: number;
  limit: number;
}

export interface SpaceListEnvelope {
  items: TenantSpace[];
  count: number;
}

export interface EmployeeCreateInput {
  employee_no: string;
  display_name: string;
  title?: string;
  hired_at?: string;
}

export interface EmployeeUpdateInput {
  display_name?: string;
  title?: string;
}

export interface AssignmentCreateInput {
  employee_id: string;
  space_id: string;
  assignment_role: string;
}

export interface AssignmentUpdateInput {
  assignment_role: string;
}

export interface EmployeeListQuery {
  status?: string;
  limit?: number;
  signal?: AbortSignal;
}

export interface AssignmentListQuery {
  employee_id?: string;
  space_id?: string;
  status?: string;
  limit?: number;
  signal?: AbortSignal;
}

// --------------------------------------------------------------------- paths
const tenantSegment = (tenantId: string) => `/company/tenants/${encodeURIComponent(tenantId)}`;

export const companyPaths = {
  employees: (tenantId: string) => `${tenantSegment(tenantId)}/employees`,
  employee: (tenantId: string, employeeId: string) =>
    `${tenantSegment(tenantId)}/employees/${encodeURIComponent(employeeId)}`,
  suspendEmployee: (tenantId: string, employeeId: string) =>
    `${tenantSegment(tenantId)}/employees/${encodeURIComponent(employeeId)}/suspend`,
  terminateEmployee: (tenantId: string, employeeId: string) =>
    `${tenantSegment(tenantId)}/employees/${encodeURIComponent(employeeId)}/terminate`,
  assignments: (tenantId: string) => `${tenantSegment(tenantId)}/assignments`,
  assignment: (tenantId: string, assignmentId: string) =>
    `${tenantSegment(tenantId)}/assignments/${encodeURIComponent(assignmentId)}`,
  endAssignment: (tenantId: string, assignmentId: string) =>
    `${tenantSegment(tenantId)}/assignments/${encodeURIComponent(assignmentId)}/end`,
  tenantSpaces: (tenantId: string) => `/tenants/${encodeURIComponent(tenantId)}/spaces`,
} as const;

/** Drop undefined query values so the URL only carries real filters. */
function query(params: Record<string, string | number | undefined>): Record<string, string | number> {
  const out: Record<string, string | number> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      out[key] = value;
    }
  }
  return out;
}

// ------------------------------------------------------------------ employee
export function listEmployees(
  client: ApiClient,
  tenantId: string,
  options: EmployeeListQuery = {},
): Promise<ListEnvelope<Employee>> {
  return client.get<ListEnvelope<Employee>>(companyPaths.employees(tenantId), {
    query: query({ status: options.status, limit: options.limit ?? COMPANY_LIST_LIMIT }),
    signal: options.signal,
  });
}

export function getEmployee(
  client: ApiClient,
  tenantId: string,
  employeeId: string,
  signal?: AbortSignal,
): Promise<Employee> {
  return client.get<Employee>(companyPaths.employee(tenantId, employeeId), { signal });
}

export function createEmployee(
  client: ApiClient,
  tenantId: string,
  input: EmployeeCreateInput,
): Promise<Employee> {
  return client.post<Employee>(companyPaths.employees(tenantId), input);
}

export function updateEmployee(
  client: ApiClient,
  tenantId: string,
  employeeId: string,
  input: EmployeeUpdateInput,
): Promise<Employee> {
  return client.patch<Employee>(companyPaths.employee(tenantId, employeeId), input);
}

export function suspendEmployee(
  client: ApiClient,
  tenantId: string,
  employeeId: string,
): Promise<Employee> {
  return client.post<Employee>(companyPaths.suspendEmployee(tenantId, employeeId), undefined);
}

export function terminateEmployee(
  client: ApiClient,
  tenantId: string,
  employeeId: string,
): Promise<Employee> {
  return client.post<Employee>(companyPaths.terminateEmployee(tenantId, employeeId), undefined);
}

// ---------------------------------------------------------------- assignment
export function listAssignments(
  client: ApiClient,
  tenantId: string,
  options: AssignmentListQuery = {},
): Promise<ListEnvelope<Assignment>> {
  return client.get<ListEnvelope<Assignment>>(companyPaths.assignments(tenantId), {
    query: query({
      employee_id: options.employee_id,
      space_id: options.space_id,
      status: options.status,
      limit: options.limit ?? COMPANY_LIST_LIMIT,
    }),
    signal: options.signal,
  });
}

export function getAssignment(
  client: ApiClient,
  tenantId: string,
  assignmentId: string,
  signal?: AbortSignal,
): Promise<Assignment> {
  return client.get<Assignment>(companyPaths.assignment(tenantId, assignmentId), { signal });
}

export function createAssignment(
  client: ApiClient,
  tenantId: string,
  input: AssignmentCreateInput,
): Promise<Assignment> {
  return client.post<Assignment>(companyPaths.assignments(tenantId), input);
}

export function updateAssignment(
  client: ApiClient,
  tenantId: string,
  assignmentId: string,
  input: AssignmentUpdateInput,
): Promise<Assignment> {
  return client.patch<Assignment>(companyPaths.assignment(tenantId, assignmentId), input);
}

export function endAssignment(
  client: ApiClient,
  tenantId: string,
  assignmentId: string,
): Promise<Assignment> {
  return client.post<Assignment>(companyPaths.endAssignment(tenantId, assignmentId), undefined);
}

// -------------------------------------------------------------------- spaces
/** Spaces the current actor may assign work to (P17 structure read). */
export function listTenantSpaces(
  client: ApiClient,
  tenantId: string,
  signal?: AbortSignal,
): Promise<SpaceListEnvelope> {
  return client.get<SpaceListEnvelope>(companyPaths.tenantSpaces(tenantId), { signal });
}
