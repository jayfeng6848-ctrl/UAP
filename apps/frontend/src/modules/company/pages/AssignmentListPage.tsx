import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Button, Card, Field, PageHeader, Select, Table } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { useFeedback } from '../../../platform/feedback/FeedbackProvider';
import {
  COMPANY_LIST_LIMIT,
  createAssignment,
  listAssignments,
  listEmployees,
  listTenantSpaces,
} from '../api';
import type { Assignment } from '../api';
import { AssignmentFormDialog } from '../components/AssignmentFormDialog';
import type { AssignmentFormValues } from '../components/AssignmentFormDialog';
import { CompanyNav } from '../components/CompanyNav';
import { CompanyEmpty, CompanyResource, TenantResolving } from '../components/CompanyStates';
import { StatusBadge } from '../components/StatusBadge';
import { useAction, useApiResource } from '../hooks';
import { companyUiPaths } from '../paths';
import { useCompanyTenant } from '../tenant';
import { ASSIGNMENT_STATUSES } from '../vocabulary';
import styles from '../company.module.css';

const OPTION_LIMIT = 100;

/** Assignment collection: real list, frozen status filter and the create action. */
export function AssignmentListPage() {
  const { client } = useAuth();
  const { notify } = useFeedback();
  const { tenantId, ready } = useCompanyTenant();
  const activeTenantId = ready ? tenantId : null;

  const [status, setStatus] = useState('');
  const [creating, setCreating] = useState(false);
  const createAction = useAction();

  const assignments = useApiResource(
    activeTenantId
      ? (signal) =>
          listAssignments(client, activeTenantId, {
            status: status === '' ? undefined : status,
            limit: COMPANY_LIST_LIMIT,
            signal,
          })
      : null,
    [client, activeTenantId, status],
  );

  // Real backend reads for the picker and for name enrichment (never a hard-coded tree).
  const options = useApiResource(
    activeTenantId
      ? async (signal) => {
          const [employees, spaces] = await Promise.all([
            listEmployees(client, activeTenantId, { limit: OPTION_LIMIT, signal }),
            listTenantSpaces(client, activeTenantId, signal),
          ]);
          return { employees: employees.items, spaces: spaces.items };
        }
      : null,
    [client, activeTenantId],
  );

  if (activeTenantId === null) {
    return <TenantResolving />;
  }

  const employeeName = (id: string) =>
    options.state.status === 'ready'
      ? options.state.data.employees.find((employee) => employee.employee_id === id)?.display_name ?? id
      : id;
  const spaceName = (id: string) =>
    options.state.status === 'ready'
      ? options.state.data.spaces.find((space) => space.id === id)?.name ?? id
      : id;

  const submitCreate = async (values: AssignmentFormValues) => {
    const ok = await createAction.run(async () => {
      await createAssignment(client, activeTenantId, {
        employee_id: values.employee_id,
        space_id: values.space_id,
        assignment_role: values.assignment_role,
      });
    });
    if (ok) {
      notify('Assignment created.', 'success');
      setCreating(false);
      assignments.reload();
    }
  };

  return (
    <section className={styles.section} data-testid="company-assignments">
      <CompanyNav tenantId={activeTenantId} />
      <PageHeader
        title="Assignments"
        description="Assignments place an employee into a space inside this tenant."
        actions={
          <Button
            onClick={() => {
              createAction.clearError();
              setCreating(true);
            }}
            data-testid="new-assignment"
          >
            New assignment
          </Button>
        }
      />
      <div className={styles.toolbar}>
        <Field label="Status">
          {({ id }) => (
            <Select id={id} value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">All statuses</option>
              {ASSIGNMENT_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      <Card>
        <CompanyResource
          state={assignments.state}
          isEmpty={(data) => data.items.length === 0}
          empty={
            <CompanyEmpty
              title="No assignments"
              description={
                status === ''
                  ? 'Assign an employee to a space to begin.'
                  : 'No assignment matches the selected status.'
              }
            />
          }
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
                      render: (row: Assignment) => employeeName(row.employee_id),
                    },
                    {
                      key: 'space',
                      header: 'Space',
                      render: (row: Assignment) => spaceName(row.space_id),
                    },
                    {
                      key: 'status',
                      header: 'Status',
                      render: (row: Assignment) => <StatusBadge status={row.status} />,
                    },
                    {
                      key: 'open',
                      header: 'Actions',
                      render: (row: Assignment) => (
                        <Link
                          className={styles.linkButton}
                          to={companyUiPaths.assignment(activeTenantId, row.assignment_id)}
                        >
                          Open
                        </Link>
                      ),
                    },
                  ]}
                  rows={data.items}
                  rowKey={(row) => row.assignment_id}
                />
              </div>
              <p className={styles.muted}>
                {data.count} record(s) · page size {data.limit}
              </p>
            </>
          )}
        </CompanyResource>
      </Card>
      <AssignmentFormDialog
        open={creating}
        mode="create"
        employees={options.state.status === 'ready' ? options.state.data.employees : []}
        spaces={options.state.status === 'ready' ? options.state.data.spaces : []}
        optionsLoading={options.state.status === 'loading' || options.state.status === 'idle'}
        optionsError={options.state.status === 'error' ? options.state.error : null}
        pending={createAction.pending}
        error={createAction.error}
        onSubmit={(values) => void submitCreate(values)}
        onCancel={() => setCreating(false)}
      />
    </section>
  );
}
