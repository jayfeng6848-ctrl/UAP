/**
 * Platform application shell (Appendix AL H13/H14).
 *
 * Layout only: global header, navigation area, main content and the global
 * feedback region. It carries no Company navigation and no Company behaviour; the
 * shell must remain usable by any future domain module.
 */

import { NavLink, Outlet } from 'react-router-dom';

import { Button } from '../../components';
import { useAuth } from '../../platform/auth/AuthContext';
import { useTenant } from '../../platform/tenant/TenantContext';

import styles from './AppShell.module.css';

export function AppShell() {
  const { status, user, logout } = useAuth();
  const { tenantId } = useTenant();

  return (
    <div className={styles.shell} data-testid="uap-app-shell">
      <header className={styles.header}>
        <span className={styles.brand}>UAP Console</span>
        <div className={styles.meta}>
          <span data-testid="uap-shell-tenant">
            Tenant: {tenantId ?? 'not selected'}
          </span>
          <span data-testid="uap-shell-user">
            User: {user?.user_id ?? 'not signed in'}
          </span>
          {status === 'authenticated' ? (
            <Button variant="secondary" size="small" onClick={() => void logout()}>
              Sign out
            </Button>
          ) : null}
        </div>
      </header>
      <div className={styles.body}>
        <nav aria-label="Primary">
          <ul>
            <li>
              <NavLink to="/">Overview</NavLink>
            </li>
          </ul>
        </nav>
        <main className={styles.main} data-testid="uap-shell-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
