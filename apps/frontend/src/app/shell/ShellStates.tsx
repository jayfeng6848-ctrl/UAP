/** Shell-level states so loading/absence never leaks into individual pages. */

import { LoadingState } from '../../components';

export function AppBootstrapLoading() {
  return (
    <div data-testid="uap-bootstrap-loading">
      <LoadingState label="正在启动 UAP…" />
    </div>
  );
}

export function TenantUnresolved({ reason }: { reason: 'missing' | 'invalid' }) {
  return (
    <section role="alert" data-testid="uap-tenant-unresolved">
      <h2>工作空间不可用</h2>
      <p>
        {reason === 'invalid'
          ? '这个地址中的工作空间标识无效。'
          : '当前视图还没有选择工作空间。'}
      </p>
    </section>
  );
}
