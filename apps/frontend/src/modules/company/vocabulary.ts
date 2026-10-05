/**
 * Company vocabulary mirrored from the frozen domain (domains/company/values.py).
 *
 * Read-only mirror for UX affordances (status filters, badges, role picker and a
 * pre-submit shape check). The backend stays authoritative: every value is
 * re-validated server-side and a rejection is surfaced as the frozen 422/409.
 */

export const EMPLOYEE_STATUSES = ['active', 'suspended', 'terminated'] as const;
export const ASSIGNMENT_STATUSES = ['active', 'ended'] as const;
export const ASSIGNMENT_ROLES = ['member', 'lead'] as const;

/** Mirrors the frozen DB CHECK ``ck_company_employees_no``. */
export const EMPLOYEE_NO_PATTERN = /^[A-Za-z0-9._-]{1,64}$/;

export type BadgeToneName = 'neutral' | 'success' | 'warning' | 'danger';

export function statusTone(status: string): BadgeToneName {
  switch (status) {
    case 'active':
      return 'success';
    case 'suspended':
      return 'warning';
    case 'terminated':
    case 'ended':
      return 'danger';
    default:
      return 'neutral';
  }
}

/** Timezone-explicit, locale-independent timestamp rendering (never a raw ISO dump). */
export function formatTimestamp(value: string | null): string {
  if (!value) {
    return '—';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return '—';
  }
  return `${parsed.toISOString().slice(0, 16).replace('T', ' ')} UTC`;
}
