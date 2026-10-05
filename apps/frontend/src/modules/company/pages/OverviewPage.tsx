import { Link } from 'react-router-dom';

import { Card, PageHeader, Table } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { listAssignments, listEmployees } from '../api';
import type { Assignment, Employee } from '../api';
import { CompanyNav } from '../components/CompanyNav';
import { CompanyEmpty, CompanyResource, TenantResolving } from '../components/CompanyStates';
import { StatusBadge } from '../components/StatusBadge';
import { useApiResource } from '../hooks';
import { companyUiPaths } from '../paths';
import { useCompanyTenant } from '../tenant';
import styles from '../company.module.css';

const RECENT_LIMIT = 5;

/** Company entry page: tenant scope, the two information areas and a recent slice. */
export function OverviewPage() {
  const { client } = useAuth();
  const { tenantId, ready } = useCompanyTenant();
  const activeTenantId = ready ? tenantId : null;

  const employees = useApiResource(
    activeTenantId
      ? (signal) => listEmployees(client, activeTenantId, { limit: RECENT_LIMIT, signal })
      : null,
    [client, activeTenantId],
  );
  const assignments = useApiResource(
    activeTenantId
      ? (signal) => listAssignments(client, activeTenantId, { limit: RECENT_LIMIT, signal })
      : null,
    [client, activeTenantId],
  );

  if (activeTenantId === null) {
    return <TenantResolving />;
  }

  return (
    <section className={styles.section} data-testid="company-overview">
      <CompanyNav tenantId={activeTenantId} />
      <PageHeader
        title="Company overview"
        description={`Tenant scope: ${activeTenantId}. Data is read from the Company API for this tenant only.`}
      />
      <Card>
        <PageHeader
          title="Recent employees"
          actions={<Link to={companyUiPaths.employees(activeTenantId)}>View all employees</Link>}
        />
        <CompanyResource
          state={employees.state}
          isEmpty={(data) => data.items.length === 0}
          empty={<CompanyEmpty title="No employees yet" description="Create the first employee record." />}
          loadingLabel="Loading employees…"
          onRetry={employees.reload}
        >
          {(data) => (
            <>
              <div className={styles.tableScroll}>
                <Table
                  columns={[
                    {
                      key: 'name',
                      header: 'Name',
                      render: (row: Employee) => (
                        <Link to={companyUiPaths.employee(activeTenantId, row.employee_id)}>
                          {row.display_name}
                        </Link>
                      ),
                    },
                    { key: 'no', header: 'Employee no', render: (row: Employee) => row.employee_no },
                    {
                      key: 'status',
                      header: 'Status',
                      render: (row: Employee) => <StatusBadge status={row.status} />,
                    },
                  ]}
                  rows={data.items}
                  rowKey={(row) => row.employee_id}
                />
              </div>
              <p className={styles.muted}>
                Showing {data.count} of at most {data.limit} records.
              </p>
            </>
          )}
        </CompanyResource>
      </Card>
      <Card>
        <PageHeader
          title="Recent assignments"
          actions={<Link to={companyUiPaths.assignments(activeTenantId)}>View all assignments</Link>}
        />
        <CompanyResource
          state={assignments.state}
          isEmpty={(data) => data.items.length === 0}
          empty={<CompanyEmpty title="No assignments yet" description="Assign an employee to a space." />}
          loadingLabel="Loading assignments…"
          onRetry={assignments.reload}
        >
          {(data) => (
            <>
              <div className={styles.tableScroll}>
                <Table
                  columns={[
                    {
                      key: 'role',
                      header: 'Role',
                      render: (row: Assignment) => (
                        <Link to={companyUiPaths.assignment(activeTenantId, row.assignment_id)}>
                          {row.assignment_role}
                        </Link>
                      ),
                    },
                    {
                      key: 'employee',
                      header: 'Employee',
                      render: (row: Assignment) => row.employee_id,
                    },
                    { key: 'space', header: 'Space', render: (row: Assignment) => row.space_id },
                    {
                      key: 'status',
                      header: 'Status',
                      render: (row: Assignment) => <StatusBadge status={row.status} />,
                    },
                  ]}
                  rows={data.items}
                  rowKey={(row) => row.assignment_id}
                />
              </div>
              <p className={styles.muted}>
                Showing {data.count} of at most {data.limit} records.
              </p>
            </>
          )}
        </CompanyResource>
      </Card>
    </section>
  );
}
