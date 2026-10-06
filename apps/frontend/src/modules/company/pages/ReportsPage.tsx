/**
 * Company operational reports (OQ-CUI-02 = A · PDL Appendix AP).
 *
 * Read-only figures derived from existing Company data through the authorized
 * report endpoint. No analytics store, no report table — and no client-side
 * computation of authority: a 403 from the backend is final.
 */

import { useCallback, useEffect, useState } from 'react';

import { Button, Card, PageHeader } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { useAuth } from '../../../platform/auth/AuthContext';
import { getOperationalReport } from '../api';
import type { OperationalReport } from '../api';
import { useCompanyTenant } from '../tenant';
import styles from '../company.module.css';

function countLine(label: string, counts: Record<string, number>): string {
  const parts = Object.entries(counts).map(([key, value]) => `${key} ${value}`);
  return parts.length > 0 ? `${label}：${parts.join(' · ')}` : `${label}：—`;
}

export function ReportsPage() {
  const { tenantId } = useCompanyTenant();
  const { client } = useAuth();
  const [report, setReport] = useState<OperationalReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (tenantId === null) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await getOperationalReport(client, tenantId));
    } catch {
      setReport(null);
      setError('暂时无法读取报表。请稍后重试，或确认你有查看公司数据的权限。');
    } finally {
      setLoading(false);
    }
  }, [client, tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (tenantId === null) {
    return (
      <Card>
        <PageHeader title="运营报表" description="正在准备工作空间…" />
      </Card>
    );
  }

  return (
    <section data-testid="company-reports">
      <PageHeader title="运营报表" description="基于现有公司数据的只读汇总。" />
      {loading ? <p data-testid="reports-loading">正在加载报表…</p> : null}
      {error ? (
        <>
          <InlineError>{error}</InlineError>
          <div className={styles.actions}>
            <Button variant="secondary" onClick={() => void load()}>
              重试
            </Button>
          </div>
        </>
      ) : null}
      {!loading && !error && report !== null ? (
        report.headcount === 0 ? (
          <p data-testid="reports-empty">还没有可统计的员工数据。</p>
        ) : (
          <Card>
            <ul data-testid="reports-body">
              <li data-testid="report-headcount">员工总数：{report.headcount}</li>
              <li data-testid="report-lifecycle">
                {countLine('在职状态', report.employee_lifecycle)}
              </li>
              <li data-testid="report-assignments">
                {countLine('分配状态', report.assignment_summary)}
              </li>
              <li data-testid="report-unassigned">未分配员工：{report.unassigned_employees}</li>
              <li data-testid="report-space-employees">
                {countLine('各部门人数', report.space_employee_counts)}
              </li>
              <li data-testid="report-space-assignments">
                {countLine('各部门分配数', report.space_assignment_counts)}
              </li>
            </ul>
          </Card>
        )
      ) : null}
    </section>
  );
}
