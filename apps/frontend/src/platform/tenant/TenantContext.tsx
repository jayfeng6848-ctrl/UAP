/**
 * Current Tenant Context (Appendix AL H03/H16/H17).
 *
 * The tenant id comes from the URL (`/tenants/:tenant_id/...`) and lives in a
 * single context. It is **context only — never an authorization credential**: the
 * backend remains the security boundary and answers 403 for tenants the caller may
 * not reach. Components never mutate the tenant directly; the route boundary owns
 * the transition so URL, context and API path can never disagree.
 */

import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

const TENANT_ID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Tenant ids follow the backend uuid id contract. */
export function isValidTenantId(value: string | undefined | null): boolean {
  return typeof value === 'string' && TENANT_ID_PATTERN.test(value);
}

export interface TenantContextValue {
  tenantId: string | null;
  setTenant: (tenantId: string) => void;
  clearTenant: () => void;
}

const TenantContext = createContext<TenantContextValue | null>(null);

export function TenantProvider({
  children,
  initialTenantId = null,
}: {
  children: ReactNode;
  initialTenantId?: string | null;
}) {
  const [tenantId, setTenantId] = useState<string | null>(initialTenantId);
  const value = useMemo<TenantContextValue>(
    () => ({
      tenantId,
      setTenant: (next: string) => setTenantId(next),
      clearTenant: () => setTenantId(null),
    }),
    [tenantId],
  );
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant(): TenantContextValue {
  const context = useContext(TenantContext);
  if (context === null) {
    throw new Error('useTenant must be used inside TenantProvider');
  }
  return context;
}
