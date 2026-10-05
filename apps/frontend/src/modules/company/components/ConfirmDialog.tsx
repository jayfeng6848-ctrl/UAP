import { Button, Dialog } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { messageForCode } from '../../../platform/api';
import type { ApiError } from '../../../platform/api';

/**
 * Confirmation for the irreversible Company actions (Suspend · Terminate · End
 * assignment). UI confirmation is UX, never authorization: the backend still
 * decides, and its 403/409 answer is rendered here.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  tone = 'danger',
  pending,
  error,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  tone?: 'primary' | 'danger';
  pending: boolean;
  error: ApiError | null;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Dialog
      open={open}
      title={title}
      description={description}
      onClose={pending ? () => undefined : onCancel}
      footer={
        <div>
          <Button variant="secondary" onClick={onCancel} disabled={pending}>
            Cancel
          </Button>{' '}
          <Button variant={tone} loading={pending} onClick={onConfirm} data-testid="confirm-action">
            {confirmLabel}
          </Button>
        </div>
      }
    >
      {error ? <InlineError>{messageForCode(error.code)}</InlineError> : null}
    </Dialog>
  );
}
