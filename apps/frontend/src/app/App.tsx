import { BrowserRouter } from 'react-router-dom';

import { AuthProvider } from '../platform/auth/AuthContext';
import type { ApiClient } from '../platform/api';
import { FeedbackProvider } from '../platform/feedback/FeedbackProvider';
import { TenantProvider } from '../platform/tenant/TenantContext';
import { AppRouter } from './routing/AppRouter';
import { ErrorBoundary } from './ErrorBoundary';

/**
 * Application composition root.
 *
 * Bootstrap order (Appendix AL H60): boot → auth bootstrap → current user →
 * route → tenant context → feature. `client` is injectable for tests.
 */
export function App({ client }: { client?: ApiClient }) {
  return (
    <ErrorBoundary>
      <FeedbackProvider>
        <AuthProvider client={client}>
          <TenantProvider>
            <BrowserRouter>
              <AppRouter />
            </BrowserRouter>
          </TenantProvider>
        </AuthProvider>
      </FeedbackProvider>
    </ErrorBoundary>
  );
}
