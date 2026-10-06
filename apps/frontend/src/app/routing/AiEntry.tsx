/**
 * Customer entry `/ai` (HD-P21-17 §3/§32): resolve the workspace from the session
 * and hand over to the tenant-scoped AI page. The customer never types a tenant id.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Card, PageHeader } from '../../components';
import { useAuth } from '../../platform/auth/AuthContext';
import { AI_COPY } from '../../modules/ai/copy';

interface MeView {
  tenant_id: string | null;
}

export function AiEntry() {
  const { client, status } = useAuth();
  const navigate = useNavigate();
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    if (status !== 'authenticated') {
      return;
    }
    let cancelled = false;
    client
      .get<MeView>('/me')
      .then((me) => {
        if (cancelled) {
          return;
        }
        if (me.tenant_id) {
          navigate(`/tenants/${me.tenant_id}/ai`, { replace: true });
          return;
        }
        setProblem(AI_COPY.entryNoWorkspace);
      })
      .catch(() => {
        if (!cancelled) {
          setProblem(AI_COPY.entryFailed);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, status, navigate]);

  return (
    <Card>
      <PageHeader title={AI_COPY.assistantTitle} description={problem ?? AI_COPY.entryResolving} />
    </Card>
  );
}
