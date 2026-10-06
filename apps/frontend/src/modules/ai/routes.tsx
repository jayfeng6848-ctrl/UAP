/** AI module route tree (HD-P21-17). Mounted under `/tenants/:tenant_id/ai/*`. */

import { Route, Routes } from 'react-router-dom';

import { AIHomePage } from './pages/AIHomePage';
import { useAiTenant } from './tenant';

export { aiPaths } from './paths';

export function AIRouteTree() {
  const { tenantId } = useAiTenant();
  return (
    <Routes>
      <Route index element={<AIHomePage tenantId={tenantId} />} />
      <Route path="assistant" element={<AIHomePage tenantId={tenantId} />} />
    </Routes>
  );
}
