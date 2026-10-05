import { useEffect, useState } from 'react';

import { Button, Dialog, Field, Select } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { messageForCode } from '../../../platform/api';
import type { ApiError } from '../../../platform/api';
import type { Assignment, Employee, TenantSpace } from '../api';
import { ASSIGNMENT_ROLES } from '../vocabulary';

export interface AssignmentFormValues {
  employee_id: string;
  space_id: string;
  assignment_role: string;
}

/**
 * Create / edit an assignment. The employee and space pickers are populated from
 * real backend reads (Company employees, P17 tenant spaces) — never from a
 * hard-coded organisation tree, and never from user-supplied free text.
 */
export function AssignmentFormDialog({
  open,
  mode,
  assignment,
  employees,
  spaces,
  optionsLoading,
  optionsError,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  mode: 'create' | 'edit';
  assignment?: Assignment;
  employees: Employee[];
  spaces: TenantSpace[];
  optionsLoading: boolean;
  optionsError: ApiError | null;
  pending: boolean;
  error: ApiError | null;
  onSubmit: (values: AssignmentFormValues) => void;
  onCancel: () => void;
}) {
  const [employeeId, setEmployeeId] = useState('');
  const [spaceId, setSpaceId] = useState('');
  const [role, setRole] = useState<string>(ASSIGNMENT_ROLES[0]);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }
    setEmployeeId(mode === 'edit' ? (assignment?.employee_id ?? '') : '');
    setSpaceId(mode === 'edit' ? (assignment?.space_id ?? '') : '');
    setRole(assignment?.assignment_role ?? ASSIGNMENT_ROLES[0]);
    setTouched(false);
  }, [open, mode, assignment]);

  const assignableSpaces = spaces.filter((space) => space.status === 'active');
  const employeeError = touched && employeeId === '' ? 'Choose an employee.' : undefined;
  const spaceError = touched && spaceId === '' ? 'Choose a space.' : undefined;

  const submit = () => {
    setTouched(true);
    if (employeeId === '' || spaceId === '') {
      return;
    }
    onSubmit({ employee_id: employeeId, space_id: spaceId, assignment_role: role });
  };

  return (
    <Dialog
      open={open}
      title={mode === 'create' ? 'New assignment' : 'Edit assignment'}
      description="An assignment places one employee into one space for this tenant."
      onClose={pending ? () => undefined : onCancel}
      footer={
        <div>
          <Button variant="secondary" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>{' '}
          <Button loading={pending} onClick={submit} data-testid="assignment-submit">
            {mode === 'create' ? 'Create assignment' : 'Save changes'}
          </Button>
        </div>
      }
    >
      {mode === 'create' ? (
        <>
          <Field label="Employee" error={employeeError}>
            {({ id }) => (
              <Select id={id} value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}>
                <option value="">{optionsLoading ? 'Loading employees…' : 'Select an employee'}</option>
                {employees.map((employee) => (
                  <option key={employee.employee_id} value={employee.employee_id}>
                    {employee.display_name} ({employee.employee_no})
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Space" error={spaceError} hint="Spaces you may assign work to in this tenant.">
            {({ id }) => (
              <Select id={id} value={spaceId} onChange={(event) => setSpaceId(event.target.value)}>
                <option value="">{optionsLoading ? 'Loading spaces…' : 'Select a space'}</option>
                {assignableSpaces.map((space) => (
                  <option key={space.id} value={space.id}>
                    {space.name} ({space.key})
                  </option>
                ))}
              </Select>
            )}
          </Field>
          {!optionsLoading && assignableSpaces.length === 0 ? (
            <p data-testid="assignment-no-spaces">
              No active space is available to assign work to.
            </p>
          ) : null}
        </>
      ) : (
        <p data-testid="assignment-target-readonly">
          Employee {assignment?.employee_id} · Space {assignment?.space_id}
        </p>
      )}
      <Field label="Assignment role">
        {({ id }) => (
          <Select id={id} value={role} onChange={(event) => setRole(event.target.value)}>
            {ASSIGNMENT_ROLES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        )}
      </Field>
      {optionsError ? <InlineError>{messageForCode(optionsError.code)}</InlineError> : null}
      {error ? <InlineError>{messageForCode(error.code)}</InlineError> : null}
    </Dialog>
  );
}
