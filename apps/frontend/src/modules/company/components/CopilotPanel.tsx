/**
 * Company AI Copilot panel (OQ-CUI-03 / 04 / 05 / 09 · PDL Appendix AP).
 *
 * Read answers are produced by the existing AI runtime; citations come from the
 * authorized backend query; high-risk actions produce an **ephemeral proposal**
 * that the human must confirm — the panel never mutates Company data itself.
 */

import { useCallback, useState } from 'react';

import { Button, Card, PageHeader, TextField } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { useAuth } from '../../../platform/auth/AuthContext';
import { confirmProposal, runCopilot } from '../api';
import type { CopilotReply } from '../api';
import { useCompanyTenant } from '../tenant';
import styles from '../company.module.css';

const COPY = {
  title: 'AI 助手',
  description: '用自然语言询问公司数据，或让我先给出变更建议。',
  question: '你的问题',
  placeholder: '例如：公司现在有多少员工？',
  ask: '提问',
  asking: '正在处理…',
  propose: '先给出建议（不直接执行）',
  citationTitle: '引用',
  confirmed: '已确认。本次变更由你本人授权，系统已重新校验当前状态。',
  confirm: '确认执行',
  stale: '当前状态已变化，这条建议已失效，请重新获取。',
  notFound: '这条建议已过期或已被使用。',
  denied: '你没有查看这部分数据的权限。',
  unavailable: 'AI 暂时不可用。请先连接 AI 服务，或稍后重试。',
  empty: '还没有提问。',
} as const;

function failureMessage(code: string | null): string {
  if (code === 'CREDENTIAL_UNAVAILABLE' || code === 'AI_UNAVAILABLE') {
    return COPY.unavailable;
  }
  if (code === 'AUTHORIZATION_DENIED' || code === 'PERMISSION_DENIED') {
    return COPY.denied;
  }
  return COPY.unavailable;
}

export function CopilotPanel() {
  const { tenantId } = useCompanyTenant();
  const { client } = useAuth();
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState<CopilotReply | null>(null);
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  const ask = useCallback(
    async (mode: 'answer' | 'propose') => {
      const text = message.trim();
      if (tenantId === null || text.length === 0 || pending) {
        return;
      }
      setPending(true);
      setNotice(null);
      setConfirmed(false);
      try {
        const result = await runCopilot(client, tenantId, text, { mode });
        setReply(result);
        if (result.status !== 'COMPLETED') {
          setNotice(failureMessage(result.failure_code));
        }
      } catch {
        setReply(null);
        setNotice(COPY.unavailable);
      } finally {
        setPending(false);
      }
    },
    [client, message, pending, tenantId],
  );

  const confirm = useCallback(async () => {
    const proposal = reply?.proposal;
    if (tenantId === null || !proposal) {
      return;
    }
    setPending(true);
    setNotice(null);
    try {
      await confirmProposal(client, tenantId, proposal.proposal_id);
      setConfirmed(true);
      setReply((current) => (current ? { ...current, proposal: null } : current));
    } catch (error) {
      const detail =
        typeof error === 'object' && error !== null && 'detail' in error
          ? String((error as { detail?: unknown }).detail)
          : '';
      setNotice(detail === 'proposal_stale' ? COPY.stale : COPY.notFound);
    } finally {
      setPending(false);
    }
  }, [client, reply, tenantId]);

  if (tenantId === null) {
    return (
      <Card>
        <PageHeader title={COPY.title} description="正在准备工作空间…" />
      </Card>
    );
  }

  return (
    <Card>
      <PageHeader title={COPY.title} description={COPY.description} />
      <TextField
        label={COPY.question}
        value={message}
        onChange={setMessage}
        placeholder={COPY.placeholder}
      />
      <div className={styles.actions}>
        <Button
          data-testid="copilot-ask"
          loading={pending}
          onClick={() => void ask('answer')}
        >
          {pending ? COPY.asking : COPY.ask}
        </Button>
        <Button
          variant="secondary"
          data-testid="copilot-propose"
          disabled={pending}
          onClick={() => void ask('propose')}
        >
          {COPY.propose}
        </Button>
      </div>
      {notice ? <InlineError>{notice}</InlineError> : null}
      {confirmed ? <p data-testid="copilot-confirmed">{COPY.confirmed}</p> : null}
      {reply === null ? <p data-testid="copilot-empty">{COPY.empty}</p> : null}
      {reply !== null ? (
        <>
          <p data-testid="copilot-status">状态：{reply.status}</p>
          {reply.citations.length > 0 ? (
            <div data-testid="copilot-citations">
              <p className={styles.muted}>{COPY.citationTitle}</p>
              <ul>
                {reply.citations.slice(0, 10).map((citation) => (
                  <li key={`${citation.type}:${citation.id}`} data-testid="copilot-citation">
                    {citation.label}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {reply.proposal ? (
            <div data-testid="copilot-proposal">
              <p>
                建议：{reply.proposal.summary}（当前：{reply.current_state}）
              </p>
              <Button
                variant="danger"
                data-testid="copilot-confirm"
                loading={pending}
                onClick={() => void confirm()}
              >
                {COPY.confirm}
              </Button>
            </div>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}
