import { Card, PageHeader } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { COMPANY_MODULE_STATUS } from '../../../modules/company';

export function HomePage() {
  const { user } = useAuth();
  return (
    <Card>
      <PageHeader
        title="UAP Console"
        description="Platform UI foundation. Domain modules arrive in separately authorized stages."
      />
      <dl>
        <dt>User</dt>
        <dd data-testid="uap-home-user">{user?.user_id ?? 'unknown'}</dd>
        <dt>Identity assurance</dt>
        <dd>{user?.authentication_assurance ?? 'unknown'}</dd>
        <dt>Company module</dt>
        <dd data-testid="uap-home-company-status">{COMPANY_MODULE_STATUS}</dd>
      </dl>
    </Card>
  );
}
