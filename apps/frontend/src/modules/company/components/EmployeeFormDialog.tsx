import { useEffect, useState } from 'react';

import { Button, Dialog, Field, Select, TextField } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { messageForCode } from '../../../platform/api';
import type { ApiError } from '../../../platform/api';
import type { Employee } from '../api';
import { EMPLOYEE_NO_PATTERN } from '../vocabulary';

export interface EmployeeFormValues {
  employee_no: string;
  display_name: string;
  title: string;
}

/**
 * Create / edit an employee. The client mirrors only the frozen shape checks
 * (required fields and the employee-number pattern from the domain); every other
 * rule — including natural-key conflicts — is decided by the backend and shown
 * here as the frozen 409/422 message.
 */
export function EmployeeFormDialog({
  open,
  mode,
  employee,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  mode: 'create' | 'edit';
  employee?: Employee;
  pending: boolean;
  error: ApiError | null;
  onSubmit: (values: EmployeeFormValues) => void;
  onCancel: () => void;
}) {
  const [employeeNo, setEmployeeNo] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [title, setTitle] = useState('');
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }
    setEmployeeNo(employee?.employee_no ?? '');
    setDisplayName(employee?.display_name ?? '');
    setTitle(employee?.title ?? '');
    setTouched(false);
  }, [open, employee]);

  const employeeNoError =
    mode === 'create' && touched && !EMPLOYEE_NO_PATTERN.test(employeeNo)
      ? 'Use 1–64 letters, digits, dot, dash or underscore.'
      : undefined;
  const displayNameError =
    touched && displayName.trim().length === 0 ? 'Display name is required.' : undefined;

  const unchanged =
    mode === 'edit' &&
    employee !== undefined &&
    displayName === (employee.display_name ?? '') &&
    title === (employee.title ?? '');

  const submit = () => {
    setTouched(true);
    if (displayName.trim().length === 0) {
      return;
    }
    if (mode === 'create' && !EMPLOYEE_NO_PATTERN.test(employeeNo)) {
      return;
    }
    if (unchanged) {
      return;
    }
    onSubmit({ employee_no: employeeNo.trim(), display_name: displayName.trim(), title: title.trim() });
  };

  return (
    <Dialog
      open={open}
      title={mode === 'create' ? 'New employee' : `Edit ${employee?.display_name ?? 'employee'}`}
      description="Employee records are tenant-scoped. An employee is not a login identity."
      onClose={pending ? () => undefined : onCancel}
      footer={
        <div>
          <Button variant="secondary" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>{' '}
          <Button
            loading={pending}
            disabled={unchanged}
            onClick={submit}
            data-testid="employee-submit"
          >
            {mode === 'create' ? 'Create employee' : 'Save changes'}
          </Button>
        </div>
      }
    >
      <TextField
        label="Employee number"
        value={employeeNo}
        error={employeeNoError}
        onChange={setEmployeeNo}
      />
      {mode === 'edit' ? (
        <p data-testid="employee-no-readonly">Employee number: {employee?.employee_no}</p>
      ) : null}
      <TextField label="Display name" value={displayName} error={displayNameError} onChange={setDisplayName} />
      <TextField label="Title (optional)" value={title} onChange={setTitle} />
      {mode === 'edit' && unchanged ? (
        <p data-testid="employee-unchanged">Change a value to save.</p>
      ) : null}
      {error ? <InlineError>{messageForCode(error.code)}</InlineError> : null}
    </Dialog>
  );
}

/** Status selector used by the employee list filter (frozen lifecycle values only). */
export function EmployeeStatusFilter({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: readonly string[];
}) {
  return (
    <Field label="Status">
      {({ id }) => (
        <Select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">All statuses</option>
          {options.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </Select>
      )}
    </Field>
  );
}
