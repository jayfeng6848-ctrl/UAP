import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';

import { useAuth } from '../../../platform/auth/AuthContext';
import { getCompanyCapabilities } from '../api';
import styles from '../company.module.css';
import { companyUiPaths } from '../paths';

/**
 * Company sub-navigation. Reports and the AI Copilot appear only when the
 * **server-projected** capability says the actor may read Company data
 * (OQ-CUI-01): the frontend consumes the projection and never computes it.
 * Hiding an entry is a UX affordance, never a permission decision — the backend
 * still authorizes every call.
 */
export function CompanyNav({ tenantId }: { tenantId: string }) {
  const { client } = useAuth();
  const [canRead, setCanRead] = useState(false);

  useEffect(() => {
    let live = true;
    getCompanyCapabilities(client, tenantId)
      .then((projection) => {
        if (live) {
          setCanRead(projection.actions['company_employee.read'] === true);
        }
      })
      .catch(() => {
        if (live) {
          setCanRead(false);
        }
      });
    return () => {
      live = false;
    };
  }, [client, tenantId]);

  const items = [
    { to: companyUiPaths.overview(tenantId), label: 'Overview', end: true },
    { to: companyUiPaths.employees(tenantId), label: 'Employees', end: false },
    { to: companyUiPaths.assignments(tenantId), label: 'Assignments', end: false },
    ...(canRead
      ? [
          { to: `/tenants/${tenantId}/company/reports`, label: '运营报表', end: false },
          { to: `/tenants/${tenantId}/company/copilot`, label: 'AI 助手', end: false },
        ]
      : []),
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
