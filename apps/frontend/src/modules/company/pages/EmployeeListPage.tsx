import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Button, Card, PageHeader, Table } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { useFeedback } from '../../../platform/feedback/FeedbackProvider';
import { COMPANY_LIST_LIMIT, createEmployee, listEmployees } from '../api';
import type { Employee } from '../api';
import { CompanyNav } from '../components/CompanyNav';
import { CompanyEmpty, CompanyResource, TenantResolving } from '../components/CompanyStates';
import { EmployeeFormDialog, EmployeeStatusFilter } from '../components/EmployeeFormDialog';
import type { EmployeeFormValues } from '../components/EmployeeFormDialog';
import { StatusBadge } from '../components/StatusBadge';
import { useAction, useApiResource } from '../hooks';
import { companyUiPaths } from '../paths';
import { useCompanyTenant } from '../tenant';
import { EMPLOYEE_STATUSES } from '../vocabulary';
import styles from '../company.module.css';

/** Employee collection: real list, frozen status filter and the create action. */
export function EmployeeListPage() {
  const { client } = useAuth();
  const { notify } = useFeedback();
  const { tenantId, ready } = useCompanyTenant();
  const activeTenantId = ready ? tenantId : null;

  const [status, setStatus] = useState('');
  const [creating, setCreating] = useState(false);
  const createAction = useAction();

  const employees = useApiResource(
    activeTenantId
      ? (signal) =>
          listEmployees(client, activeTenantId, {
            status: status === '' ? undefined : status,
            limit: COMPANY_LIST_LIMIT,
            signal,
          })
      : null,
    [client, activeTenantId, status],
  );

  if (activeTenantId === null) {
    return <TenantResolving />;
  }

  const submitCreate = async (values: EmployeeFormValues) => {
    const ok = await createAction.run(async () => {
      await createEmployee(client, activeTenantId, {
        employee_no: values.employee_no,
        display_name: values.display_name,
        ...(values.title === '' ? {} : { title: values.title }),
      });
    });
    if (ok) {
      notify('Employee created.', 'success');
      setCreating(false);
      employees.reload();
    }
  };

  return (
    <section className={styles.section} data-testid="company-employees">
      <CompanyNav tenantId={activeTenantId} />
      <PageHeader
        title="Employees"
        description="Employee records in this tenant. An employee is not a login identity."
        actions={
          <Button
            onClick={() => {
              createAction.clearError();
              setCreating(true);
            }}
            data-testid="new-employee"
          >
            New employee
          </Button>
        }
      />
      <div className={styles.toolbar}>
        <EmployeeStatusFilter value={status} onChange={setStatus} options={EMPLOYEE_STATUSES} />
      </div>
      <Card>
        <CompanyResource
          state={employees.state}
          isEmpty={(data) => data.items.length === 0}
          empty={
            <CompanyEmpty
              title="No employees"
              description={
                status === ''
                  ? 'Create the first employee record for this tenant.'
                  : 'No employee matches the selected status.'
              }
            />
          }
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
                    { key: 'title', header: 'Title', render: (row: Employee) => row.title ?? '—' },
                    {
                      key: 'status',
                      header: 'Status',
                      render: (row: Employee) => <StatusBadge status={row.status} />,
                    },
                    {
                      key: 'open',
                      header: 'Actions',
                      render: (row: Employee) => (
                        <Link
                          className={styles.linkButton}
                          to={companyUiPaths.employee(activeTenantId, row.employee_id)}
                        >
                          Open
                        </Link>
                      ),
                    },
                  ]}
                  rows={data.items}
                  rowKey={(row) => row.employee_id}
                />
              </div>
              <p className={styles.muted}>
                {data.count} record(s) · page size {data.limit}
              </p>
            </>
          )}
        </CompanyResource>
      </Card>
      <EmployeeFormDialog
        open={creating}
        mode="create"
        pending={createAction.pending}
        error={createAction.error}
        onSubmit={(values) => void submitCreate(values)}
        onCancel={() => setCreating(false)}
      />
    </section>
  );
}
