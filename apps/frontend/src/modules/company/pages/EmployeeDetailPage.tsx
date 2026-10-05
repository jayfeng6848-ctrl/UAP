import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { Button, Card, PageHeader, Table } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { useFeedback } from '../../../platform/feedback/FeedbackProvider';
import {
  getEmployee,
  listAssignments,
  suspendEmployee,
  terminateEmployee,
  updateEmployee,
} from '../api';
import type { Assignment } from '../api';
import { CompanyNav } from '../components/CompanyNav';
import { CompanyEmpty, CompanyError, CompanyLoading, TenantResolving } from '../components/CompanyStates';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { EmployeeFormDialog } from '../components/EmployeeFormDialog';
import type { EmployeeFormValues } from '../components/EmployeeFormDialog';
import { StatusBadge } from '../components/StatusBadge';
import { useAction, useApiResource } from '../hooks';
import { companyUiPaths } from '../paths';
import { useCompanyTenant } from '../tenant';
import { formatTimestamp } from '../vocabulary';
import styles from '../company.module.css';

/** Employee detail: profile, lifecycle actions (with confirmation) and assignments. */
export function EmployeeDetailPage() {
  const { client } = useAuth();
  const { notify } = useFeedback();
  const params = useParams<{ employee_id?: string }>();
  const employeeId = params.employee_id ?? '';
  const { tenantId, ready } = useCompanyTenant();
  const activeTenantId = ready ? tenantId : null;

  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState<'suspend' | 'terminate' | null>(null);
  const editAction = useAction();
  const lifecycleAction = useAction();

  const employee = useApiResource(
    activeTenantId !== null && employeeId !== ''
      ? (signal) => getEmployee(client, activeTenantId, employeeId, signal)
      : null,
    [client, activeTenantId, employeeId],
  );
  const assignments = useApiResource(
    activeTenantId !== null && employeeId !== ''
      ? (signal) =>
          listAssignments(client, activeTenantId, { employee_id: employeeId, limit: 10, signal })
      : null,
    [client, activeTenantId, employeeId],
  );

  if (activeTenantId === null || employeeId === '') {
    return <TenantResolving />;
  }

  const nav = <CompanyNav tenantId={activeTenantId} />;

  if (employee.state.status === 'idle' || employee.state.status === 'loading') {
    return (
      <section className={styles.section}>
        {nav}
        <CompanyLoading label="Loading employee…" />
      </section>
    );
  }

  if (employee.state.status === 'error') {
    return (
      <section className={styles.section}>
        {nav}
        <PageHeader title="Employee" description={`Tenant ${activeTenantId}`} />
        <CompanyError error={employee.state.error} onRetry={employee.reload} />
      </section>
    );
  }

  const data = employee.state.data;

  const saveEdit = async (values: EmployeeFormValues) => {
    const ok = await editAction.run(async () => {
      const payload: { display_name?: string; title?: string } = {};
      if (values.display_name !== data.display_name) {
        payload.display_name = values.display_name;
      }
      if (values.title !== (data.title ?? '')) {
        payload.title = values.title;
      }
      await updateEmployee(client, activeTenantId, data.employee_id, payload);
    });
    if (ok) {
      notify('Employee updated.', 'success');
      setEditing(false);
      employee.reload();
    }
  };

  const runLifecycle = async (action: 'suspend' | 'terminate') => {
    const ok = await lifecycleAction.run(async () => {
      if (action === 'suspend') {
        await suspendEmployee(client, activeTenantId, data.employee_id);
      } else {
        await terminateEmployee(client, activeTenantId, data.employee_id);
      }
    });
    if (ok) {
      notify(action === 'suspend' ? 'Employee suspended.' : 'Employee terminated.', 'success');
      setConfirming(null);
      employee.reload();
    }
  };

  return (
    <section className={styles.section} data-testid="company-employee-detail">
      {nav}
      <PageHeader
        title={data.display_name}
        description={`Employee ${data.employee_no} · tenant ${data.tenant_id}`}
        actions={
          <div className={styles.actions}>
            <Button
              variant="secondary"
              onClick={() => {
                editAction.clearError();
                setEditing(true);
              }}
              data-testid="edit-employee"
            >
              Edit
            </Button>
            <Button
              variant="secondary"
              disabled={data.status !== 'active'}
              onClick={() => {
                lifecycleAction.clearError();
                setConfirming('suspend');
              }}
              data-testid="suspend-employee"
            >
              Suspend
            </Button>
            <Button
              variant="danger"
              disabled={data.status === 'terminated'}
              onClick={() => {
                lifecycleAction.clearError();
                setConfirming('terminate');
              }}
              data-testid="terminate-employee"
            >
              Terminate
            </Button>
          </div>
        }
      />
      <Card>
        <dl className={styles.definition}>
          <dt>Status</dt>
          <dd>
            <StatusBadge status={data.status} />
          </dd>
          <dt>Employee number</dt>
          <dd>{data.employee_no}</dd>
          <dt>Title</dt>
          <dd>{data.title ?? '—'}</dd>
          <dt>Bound user</dt>
          <dd>{data.user_id ?? '— (binding is a separate authorized action)'}</dd>
          <dt>Hired at</dt>
          <dd>{formatTimestamp(data.hired_at)}</dd>
          <dt>Terminated at</dt>
          <dd>{formatTimestamp(data.terminated_at)}</dd>
          <dt>Created</dt>
          <dd>{formatTimestamp(data.created_at)}</dd>
          <dt>Updated</dt>
          <dd>{formatTimestamp(data.updated_at)}</dd>
        </dl>
      </Card>
      <Card>
        <PageHeader title="Assignments" description="Assignments recorded for this employee." />
        {assignments.state.status === 'error' ? (
          <CompanyError error={assignments.state.error} onRetry={assignments.reload} />
        ) : assignments.state.status === 'ready' && assignments.state.data.items.length === 0 ? (
          <CompanyEmpty title="No assignments" description="This employee has no assignment in this tenant." />
        ) : assignments.state.status === 'ready' ? (
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
                { key: 'space', header: 'Space', render: (row: Assignment) => row.space_id },
                {
                  key: 'status',
                  header: 'Status',
                  render: (row: Assignment) => <StatusBadge status={row.status} />,
                },
              ]}
              rows={assignments.state.data.items}
              rowKey={(row) => row.assignment_id}
            />
          </div>
        ) : (
          <CompanyLoading label="Loading assignments…" />
        )}
      </Card>
      <EmployeeFormDialog
        open={editing}
        mode="edit"
        employee={data}
        pending={editAction.pending}
        error={editAction.error}
        onSubmit={(values) => void saveEdit(values)}
        onCancel={() => setEditing(false)}
      />
      <ConfirmDialog
        open={confirming === 'suspend'}
        title="Suspend employee"
        description={`Suspend ${data.display_name}? The record is kept; the employee cannot be assigned new work until a reactivation path exists.`}
        confirmLabel="Suspend"
        pending={lifecycleAction.pending}
        error={confirming === 'suspend' ? lifecycleAction.error : null}
        onConfirm={() => void runLifecycle('suspend')}
        onCancel={() => setConfirming(null)}
      />
      <ConfirmDialog
        open={confirming === 'terminate'}
        title="Terminate employee"
        description={`Terminate ${data.display_name}? Termination is terminal — re-hiring creates a new employee record.`}
        confirmLabel="Terminate"
        pending={lifecycleAction.pending}
        error={confirming === 'terminate' ? lifecycleAction.error : null}
        onConfirm={() => void runLifecycle('terminate')}
        onCancel={() => setConfirming(null)}
      />
    </section>
  );
}
