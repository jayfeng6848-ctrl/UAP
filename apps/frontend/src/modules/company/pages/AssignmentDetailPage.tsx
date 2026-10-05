import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { Button, Card, PageHeader } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { useFeedback } from '../../../platform/feedback/FeedbackProvider';
import { endAssignment, getAssignment, updateAssignment } from '../api';
import { AssignmentFormDialog } from '../components/AssignmentFormDialog';
import type { AssignmentFormValues } from '../components/AssignmentFormDialog';
import { CompanyNav } from '../components/CompanyNav';
import { CompanyError, CompanyLoading, TenantResolving } from '../components/CompanyStates';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { StatusBadge } from '../components/StatusBadge';
import { useAction, useApiResource } from '../hooks';
import { useCompanyTenant } from '../tenant';
import { formatTimestamp } from '../vocabulary';
import styles from '../company.module.css';

/** Assignment detail: target, role edit and the terminal end action. */
export function AssignmentDetailPage() {
  const { client } = useAuth();
  const { notify } = useFeedback();
  const params = useParams<{ assignment_id?: string }>();
  const assignmentId = params.assignment_id ?? '';
  const { tenantId, ready } = useCompanyTenant();
  const activeTenantId = ready ? tenantId : null;

  const [editing, setEditing] = useState(false);
  const [confirmingEnd, setConfirmingEnd] = useState(false);
  const editAction = useAction();
  const endAction = useAction();

  const assignment = useApiResource(
    activeTenantId !== null && assignmentId !== ''
      ? (signal) => getAssignment(client, activeTenantId, assignmentId, signal)
      : null,
    [client, activeTenantId, assignmentId],
  );

  if (activeTenantId === null || assignmentId === '') {
    return <TenantResolving />;
  }

  const nav = <CompanyNav tenantId={activeTenantId} />;

  if (assignment.state.status === 'idle' || assignment.state.status === 'loading') {
    return (
      <section className={styles.section}>
        {nav}
        <CompanyLoading label="Loading assignment…" />
      </section>
    );
  }

  if (assignment.state.status === 'error') {
    return (
      <section className={styles.section}>
        {nav}
        <PageHeader title="Assignment" description={`Tenant ${activeTenantId}`} />
        <CompanyError error={assignment.state.error} onRetry={assignment.reload} />
      </section>
    );
  }

  const data = assignment.state.data;

  const saveRole = async (values: AssignmentFormValues) => {
    const ok = await editAction.run(async () => {
      await updateAssignment(client, activeTenantId, data.assignment_id, {
        assignment_role: values.assignment_role,
      });
    });
    if (ok) {
      notify('Assignment updated.', 'success');
      setEditing(false);
      assignment.reload();
    }
  };

  const runEnd = async () => {
    const ok = await endAction.run(async () => {
      await endAssignment(client, activeTenantId, data.assignment_id);
    });
    if (ok) {
      notify('Assignment ended.', 'success');
      setConfirmingEnd(false);
      assignment.reload();
    }
  };

  return (
    <section className={styles.section} data-testid="company-assignment-detail">
      {nav}
      <PageHeader
        title={`Assignment · ${data.assignment_role}`}
        description={`Tenant ${data.tenant_id}`}
        actions={
          <div className={styles.actions}>
            <Button
              variant="secondary"
              disabled={data.status !== 'active'}
              onClick={() => {
                editAction.clearError();
                setEditing(true);
              }}
              data-testid="edit-assignment"
            >
              Edit role
            </Button>
            <Button
              variant="danger"
              disabled={data.status !== 'active'}
              onClick={() => {
                endAction.clearError();
                setConfirmingEnd(true);
              }}
              data-testid="end-assignment"
            >
              End assignment
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
          <dt>Employee</dt>
          <dd>{data.employee_id}</dd>
          <dt>Space</dt>
          <dd>{data.space_id}</dd>
          <dt>Role</dt>
          <dd>{data.assignment_role}</dd>
          <dt>Started at</dt>
          <dd>{formatTimestamp(data.started_at)}</dd>
          <dt>Ended at</dt>
          <dd>{formatTimestamp(data.ended_at)}</dd>
          <dt>Created</dt>
          <dd>{formatTimestamp(data.created_at)}</dd>
          <dt>Updated</dt>
          <dd>{formatTimestamp(data.updated_at)}</dd>
        </dl>
      </Card>
      <AssignmentFormDialog
        open={editing}
        mode="edit"
        assignment={data}
        employees={[]}
        spaces={[]}
        optionsLoading={false}
        optionsError={null}
        pending={editAction.pending}
        error={editAction.error}
        onSubmit={(values) => void saveRole(values)}
        onCancel={() => setEditing(false)}
      />
      <ConfirmDialog
        open={confirmingEnd}
        title="End assignment"
        description="Ending an assignment is terminal — a new assignment is created instead of re-opening this one."
        confirmLabel="End assignment"
        pending={endAction.pending}
        error={endAction.error}
        onConfirm={() => void runEnd()}
        onCancel={() => setConfirmingEnd(false)}
      />
    </section>
  );
}
