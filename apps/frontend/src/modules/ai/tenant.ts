/** AI tenant guard — mirrors the company guard: ready only when URL === context. */

import { useParams } from 'react-router-dom';

import { isValidTenantId, useTenant } from '../../platform/tenant/TenantContext';

export interface AiTenant {
  tenantId: string | null;
  ready: boolean;
}

export function useAiTenant(): AiTenant {
  const params = useParams<{ tenant_id?: string }>();
  const { tenantId: contextTenantId } = useTenant();
  const raw = params.tenant_id;
  const urlTenantId = typeof raw === 'string' && isValidTenantId(raw) ? raw : null;
  return { tenantId: urlTenantId, ready: urlTenantId !== null && urlTenantId === contextTenantId };
}
