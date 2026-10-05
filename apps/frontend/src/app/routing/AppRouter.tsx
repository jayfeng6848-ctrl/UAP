import { Route, Routes } from 'react-router-dom';

import { CompanyRouteTree } from '../../modules/company';
import { AppShell } from '../shell/AppShell';
import { RequireAuth } from './RequireAuth';
import { TenantBoundary } from './TenantBoundary';
import { ForbiddenPage } from './pages/ForbiddenPage';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ROUTES } from './routes';

export function AppRouter() {
  return (
    <Routes>
      <Route path={ROUTES.login} element={<LoginPage />} />
      <Route element={<AppShell />}>
        <Route
          path={ROUTES.home}
          element={
            <RequireAuth>
              <HomePage />
            </RequireAuth>
          }
        />
        <Route
          path={`${ROUTES.company}/*`}
          element={
            <RequireAuth>
              <TenantBoundary>
                <CompanyRouteTree />
              </TenantBoundary>
            </RequireAuth>
          }
        />
        <Route path={ROUTES.forbidden} element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
