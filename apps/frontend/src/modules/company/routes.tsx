/**
 * Company module route table (HD-P21-01 · Appendix AL H03/H08/H59).
 *
 * The module owns its routes and path helpers; the application mounts this tree
 * inside the platform auth + tenant boundaries. Paths follow the frozen canonical
 * form (Appendix AL.5): the module entry `/company` is the Company overview, and
 * the HD page list (`.../company/overview`) is served by that same entry.
 */

import { Route, Routes } from 'react-router-dom';

import { useCompanyTenant } from './tenant';
import { AssignmentDetailPage } from './pages/AssignmentDetailPage';
import { AssignmentListPage } from './pages/AssignmentListPage';
import { EmployeeDetailPage } from './pages/EmployeeDetailPage';
import { EmployeeListPage } from './pages/EmployeeListPage';
import { CompanyNotFoundPage } from './pages/CompanyNotFoundPage';
import { OverviewPage } from './pages/OverviewPage';

export { companyUiPaths } from './paths';

/** Mounted by the application router under `/tenants/:tenant_id/company/*`. */
export function CompanyRouteTree() {
  const { tenantId } = useCompanyTenant();
  return (
    <Routes>
      <Route index element={<OverviewPage />} />
      <Route path="employees" element={<EmployeeListPage />} />
      <Route path="employees/:employee_id" element={<EmployeeDetailPage />} />
      <Route path="assignments" element={<AssignmentListPage />} />
      <Route path="assignments/:assignment_id" element={<AssignmentDetailPage />} />
      <Route
        path="*"
        element={tenantId === null ? null : <CompanyNotFoundPage tenantId={tenantId} />}
      />
    </Routes>
  );
}
