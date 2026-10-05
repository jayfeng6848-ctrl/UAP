/** Company module path helpers (single place that builds Company addresses). */

const tenantBase = (tenantId: string) => `/tenants/${encodeURIComponent(tenantId)}/company`;

export const companyUiPaths = {
  /** Module entry — the Company overview (HD page list `.../company/overview`). */
  overview: (tenantId: string) => tenantBase(tenantId),
  employees: (tenantId: string) => `${tenantBase(tenantId)}/employees`,
  employee: (tenantId: string, employeeId: string) =>
    `${tenantBase(tenantId)}/employees/${encodeURIComponent(employeeId)}`,
  assignments: (tenantId: string) => `${tenantBase(tenantId)}/assignments`,
  assignment: (tenantId: string, assignmentId: string) =>
    `${tenantBase(tenantId)}/assignments/${encodeURIComponent(assignmentId)}`,
} as const;
