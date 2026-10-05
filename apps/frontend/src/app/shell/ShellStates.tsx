/** Shell-level states so loading/absence never leaks into individual pages. */

import { LoadingState } from '../../components';

export function AppBootstrapLoading() {
  return (
    <div data-testid="uap-bootstrap-loading">
      <LoadingState label="Starting UAP Console…" />
    </div>
  );
}

export function TenantUnresolved({ reason }: { reason: 'missing' | 'invalid' }) {
  return (
    <section role="alert" data-testid="uap-tenant-unresolved">
      <h2>Tenant context unavailable</h2>
      <p>
        {reason === 'invalid'
          ? 'The tenant in this address is not a valid identifier.'
          : 'No tenant is selected for this view.'}
      </p>
    </section>
  );
}
