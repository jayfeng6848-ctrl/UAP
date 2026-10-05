/**
 * Company tenant resolution guard (HD-P21-01 · Appendix AL.6).
 *
 * The URL is the tenant authority; the platform mirrors it into the tenant context
 * one commit later (`TenantBoundary` uses an effect). Company pages must never
 * fetch or render data for a tenant that is not the one in the address, so this
 * hook reports `ready` only when the context has caught up with the URL.
 *
 * Consequences guaranteed by the pages that consume it:
 *   * no request is issued while resolving (no wrong-tenant request)
 *   * during a tenant switch the previous tenant's data is not rendered
 *     (no stale-tenant rendering, no cross-tenant leakage)
 */

import { useParams } from 'react-router-dom';

import { isValidTenantId, useTenant } from '../../platform/tenant/TenantContext';

export interface CompanyTenant {
  /** The tenant id taken from the URL, or null when the address is not a valid tenant route. */
  tenantId: string | null;
  /** True only when URL tenant === tenant context (safe to load and render). */
  ready: boolean;
}

export function useCompanyTenant(): CompanyTenant {
  const params = useParams<{ tenant_id?: string }>();
  const { tenantId: contextTenantId } = useTenant();
  const raw = params.tenant_id;
  const urlTenantId = typeof raw === 'string' && isValidTenantId(raw) ? raw : null;

  return {
    tenantId: urlTenantId,
    ready: urlTenantId !== null && urlTenantId === contextTenantId,
  };
}
