import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from '../../platform/auth/AuthContext';
import { AppBootstrapLoading } from '../shell/ShellStates';

/** Protected-route boundary: auth state is resolved once, before any page renders. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'bootstrapping' || status === 'refreshing') {
    return <AppBootstrapLoading />;
  }
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
