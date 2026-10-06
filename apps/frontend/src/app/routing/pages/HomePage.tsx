import { Card, PageHeader } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { COMPANY_MODULE_STATUS } from '../../../modules/company';

export function HomePage() {
  const { user } = useAuth();
  return (
    <Card>
      <PageHeader
        title="工作台"
        description="这是 UAP 的平台界面。各业务模块会在各自获批的阶段陆续上线。"
      />
      <dl>
        <dt>用户</dt>
        <dd data-testid="uap-home-user">{user?.user_id ?? '未知'}</dd>
        <dt>身份验证</dt>
        <dd>{user?.authentication_assurance ?? '未知'}</dd>
        <dt>公司模块</dt>
        <dd data-testid="uap-home-company-status">
          {COMPANY_MODULE_STATUS === 'IMPLEMENTED' ? '已上线' : COMPANY_MODULE_STATUS}
        </dd>
      </dl>
    </Card>
  );
}
