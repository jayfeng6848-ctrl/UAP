/**
 * Company module boundary (HD-P21-01 · Appendix AL H14/H42).
 *
 * The module owns Company pages, Company hooks, the Company API adapter, its DTO
 * mapping, its route table and its UX vocabulary. It duplicates nothing from the
 * platform: auth, tenant context, the typed API client, the error system, the
 * design system and routing all come from `platform/` and `components/`.
 */

export const COMPANY_MODULE_STATUS = 'IMPLEMENTED' as const;

export const COMPANY_MODULE_SCOPE = [
  'Overview',
  'Employee list',
  'Employee detail',
  'Assignment list',
  'Assignment detail',
] as const;

export { CompanyRouteTree } from './routes';
export { companyUiPaths } from './paths';
