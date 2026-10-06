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
        <span className={styles.brand}>UAP</span>
        <div className={styles.meta}>
          <span data-testid="uap-shell-tenant">
            工作空间：{tenantId ?? '未选择'}
          </span>
          <span data-testid="uap-shell-user">
            用户：{user?.user_id ?? '未登录'}
          </span>
          {status === 'authenticated' ? (
            <Button variant="secondary" size="small" onClick={() => void logout()}>
              退出登录
            </Button>
          ) : null}
        </div>
      </header>
      <div className={styles.body}>
        <nav aria-label="主导航">
          <ul>
            <li>
              <NavLink to="/">总览</NavLink>
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
