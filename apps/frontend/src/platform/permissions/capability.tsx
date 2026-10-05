/**
 * Permission UX boundary (Appendix AL H09/H40/H41).
 *
 * There is deliberately **no frontend ACL engine**: the platform exposes no
 * "my permissions" endpoint, and the frontend must never infer permissions from a
 * role name, a scope string or an "admin means all" shortcut. A capability hint
 * may only affect presentation; the backend decides, and `403` is final.
 */

import type { ReactNode } from 'react';

export type CapabilityAvailability = 'unknown' | 'unavailable';

/**
 * Availability of permission data for UX decisions.
 *
 * Always `unknown` today: the frontend holds no permission source, so callers must
 * degrade gracefully (render, then reflect the backend's answer).
 */
export function capabilityAvailability(): CapabilityAvailability {
  return 'unknown';
}

export function CapabilityHint({
  children,
  availability = capabilityAvailability(),
}: {
  children: ReactNode;
  availability?: CapabilityAvailability;
}) {
  if (availability === 'unavailable') {
    return null;
  }
  return <>{children}</>;
}
