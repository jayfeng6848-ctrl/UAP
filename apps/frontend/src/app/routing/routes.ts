/**
 * Route table (Appendix AL H03/H08/H15).
 *
 * Tenant lives in the URL: `/tenants/:tenant_id/company/...`. These constants are
 * the single registration boundary — domain modules build their routes from here
 * instead of mutating the global router configuration.
 */

export const ROUTES = {
  home: '/',
  login: '/login',
  forbidden: '/403',
  company: '/tenants/:tenant_id/company',
} as const;

export const TENANT_PARAM = 'tenant_id';

export function companyPath(tenantId: string): string {
  return `/tenants/${encodeURIComponent(tenantId)}/company`;
}
