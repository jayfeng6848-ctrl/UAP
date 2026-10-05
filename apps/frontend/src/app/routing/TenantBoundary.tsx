/**
 * Tenant boundary (Appendix AL H16/H17/H18).
 *
 * The URL is the only source of the tenant. The boundary validates the identifier
 * and mirrors it into the tenant context for the subtree; invalid identifiers never
 * reach a page. It never performs authorization — the backend answers 403.
 */

import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { useParams } from 'react-router-dom';

import { TENANT_PARAM } from './routes';
import { isValidTenantId, useTenant } from '../../platform/tenant/TenantContext';
import { TenantUnresolved } from '../shell/ShellStates';

export function TenantBoundary({ children }: { children: ReactNode }) {
  const params = useParams();
  const rawTenantId = params[TENANT_PARAM];
  const valid = isValidTenantId(rawTenantId);
  const { setTenant, clearTenant } = useTenant();

  useEffect(() => {
    if (valid && rawTenantId) {
      setTenant(rawTenantId);
    } else {
      clearTenant();
    }
    return () => clearTenant();
  }, [valid, rawTenantId, setTenant, clearTenant]);

  if (!valid) {
    return <TenantUnresolved reason={rawTenantId ? 'invalid' : 'missing'} />;
  }
  return <>{children}</>;
}
