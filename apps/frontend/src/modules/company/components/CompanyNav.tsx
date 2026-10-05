import { NavLink } from 'react-router-dom';

import styles from '../company.module.css';
import { companyUiPaths } from '../paths';

/** Company sub-navigation: the module's own three information areas. */
export function CompanyNav({ tenantId }: { tenantId: string }) {
  const items = [
    { to: companyUiPaths.overview(tenantId), label: 'Overview', end: true },
    { to: companyUiPaths.employees(tenantId), label: 'Employees', end: false },
    { to: companyUiPaths.assignments(tenantId), label: 'Assignments', end: false },
  ];
  return (
    <nav aria-label="Company" className={styles.nav} data-testid="company-nav">
      <ul>
        {items.map((item) => (
          <li key={item.label}>
            <NavLink
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? styles.navActive : undefined)}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
