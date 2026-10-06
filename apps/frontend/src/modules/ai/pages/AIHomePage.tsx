/**
 * Customer AI page — Simplified Chinese default (HD-P21-18 · HD-P21-AI-01..04).
 *
 * HD-P21-AI-04 freezes the customer flow:
 *   选择服务 → 选择模型 → 输入必要信息 → 一键启用 → AI 已准备好
 * Provider and model are two independent choices. Every customer-visible string
 * comes from `AI_COPY`; no internal identifier, code or term is shown. The browser
 * never talks to a local AI endpoint — only the UAP backend does (§13).
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { Button, Card, Dialog, Field, Input, PageHeader, TextField } from '../../../components';
import { InlineError } from '../../../platform/feedback/states';
import { useAuth } from '../../../platform/auth/AuthContext';
import {
  assistantErrorMessage,
  connectAI,
  connectErrorMessage,
  detectLocalProviders,
  disconnectAI,
  getConnection,
  listProviderModels,
  listProviders,
  sendAIMessage,
} from '../api';
import type {
  ConnectionStatus,
  CustomerProvider,
  LocalProviderStatus,
  ProviderModel,
} from '../api';
import { AI_COPY } from '../copy';
import styles from '../ai.module.css';

type Stage =
  | 'loading'
  | 'welcome'
  | 'provider'
  | 'model'
  | 'credential'
  | 'connecting'
  | 'success'
  | 'assistant';

export function AIHomePage({ tenantId }: { tenantId: string | null }) {
  const { client } = useAuth();
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [stage, setStage] = useState<Stage>('loading');
  const [error, setError] = useState<string | null>(null);
  const [cleared, setCleared] = useState(false);

  const [providers, setProviders] = useState<CustomerProvider[]>([]);
  const [localStatus, setLocalStatus] = useState<LocalProviderStatus[]>([]);
  const [localBusy, setLocalBusy] = useState(false);
  const [provider, setProvider] = useState<CustomerProvider | null>(null);
  const [models, setModels] = useState<ProviderModel[]>([]);
  const [modelsBusy, setModelsBusy] = useState(false);
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');

  useEffect(() => {
    document.title =
      stage === 'assistant' || stage === 'success' ? AI_COPY.pageTitleAssistant : AI_COPY.pageTitleConnect;
  }, [stage]);

  const load = useCallback(async () => {
    if (tenantId === null) {
      return;
    }
    setStage('loading');
    setError(null);
    try {
      const [current, list] = await Promise.all([getConnection(client), listProviders(client)]);
      setStatus(current);
      setProviders(list.providers);
      setStage(current.connected ? 'assistant' : 'welcome');
    } catch {
      setError(AI_COPY.errorConfig);
      setStage('welcome');
    }
  }, [client, tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

  // HD-P21-AI-04 §6/§7: the model list is always fetched for the chosen service.
  useEffect(() => {
    if (stage !== 'model' || provider === null) {
      return;
    }
    let cancelled = false;
    setModelsBusy(true);
    setError(null);
    listProviderModels(client, provider.key)
      .then((result) => {
        if (!cancelled) {
          setModels(
            result.models.map((entry) => ({
              key: entry.key,
              display_name: entry.display_name || entry.key,
            })),
          );
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(connectErrorMessage(cause));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setModelsBusy(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [stage, provider, client]);

  const chooseProvider = useCallback(
    async (next: CustomerProvider) => {
      setProvider(next);
      setModel('');
      setModels([]);
      setError(null);
      if (next.locality === 'local') {
        // §13: detection is a backend call; the browser never probes localhost.
        setLocalBusy(true);
        try {
          const detected = await detectLocalProviders(client);
          setLocalStatus(detected.providers);
          const entry = detected.providers.find((item) => item.key === next.key);
          if (entry === undefined || !entry.available) {
            setError(
              entry?.auth_required === true
                ? AI_COPY.errorLocalAuthRequired
                : AI_COPY.localUnavailable,
            );
            setLocalBusy(false);
            return;
          }
        } catch {
          setError(AI_COPY.errorLocalUnavailable);
          setLocalBusy(false);
          return;
        }
        setLocalBusy(false);
      }
      setStage('model');
    },
    [client],
  );

  const connect = useCallback(async () => {
    if (provider === null || model === '') {
      return;
    }
    const key = apiKey.trim();
    if (provider.auth === 'required' && key.length < 8) {
      setError(AI_COPY.keyRequired);
      return;
    }
    // §8: the key must not linger in the DOM after submission.
    setApiKey('');
    setStage('connecting');
    setError(null);
    try {
      const result = await connectAI(client, provider.key, model, key);
      setStatus({
        connected: true,
        provider: result.provider,
        model: result.model,
        expires_at: result.expires_at,
        assistant_ready: true,
        ttl_seconds: result.ttl_seconds,
      });
      setStage('success');
    } catch (cause: unknown) {
      setError(connectErrorMessage(cause));
      setStage('credential');
    }
  }, [client, provider, model, apiKey]);

  const clearConnection = useCallback(async () => {
    try {
      await disconnectAI(client);
    } catch {
      /* clearing locally is best effort; the backend still holds the truth */
    }
    setStatus((current) => (current ? { ...current, connected: false, model: null } : current));
    setCleared(true);
    setProvider(null);
    setModel('');
    setStage('welcome');
  }, [client]);

  if (tenantId === null) {
    return (
      <Card>
        <PageHeader title={AI_COPY.assistantTitle} description={AI_COPY.pendingTenant} />
      </Card>
    );
  }

  const cloudProviders = providers.filter((item) => item.locality !== 'local');
  const localProviders = providers.filter((item) => item.locality === 'local');
  const keyNeeded = provider !== null && provider.auth !== 'none';
  const selectedLine = provider === null ? '' : `${provider.display_name} · ${model}`;

  return (
    <section className={styles.section} data-testid="ai-home">
      <PageHeader title={AI_COPY.homeTitle} description={AI_COPY.homeDescription} />
      {cleared && stage === 'welcome' ? <InlineError>{AI_COPY.cleared}</InlineError> : null}
      {error && stage !== 'credential' && stage !== 'connecting' ? (
        <InlineError>{error}</InlineError>
      ) : null}

      {stage === 'loading' ? <p data-testid="ai-loading">{AI_COPY.checking}</p> : null}

      {stage === 'welcome' ? (
        <Card>
          <PageHeader title={AI_COPY.welcomeTitle} description={AI_COPY.welcomeBody} />
          <p className={styles.status} data-testid="ai-status">
            {AI_COPY.statusDisconnected}
          </p>
          <div className={styles.actions}>
            <Button data-testid="ai-start" onClick={() => setStage('provider')}>
              {AI_COPY.startConnect}
            </Button>
          </div>
        </Card>
      ) : null}

      {stage === 'provider' ? (
        <Card>
          <PageHeader
            title={AI_COPY.stepProviderTitle}
            description={AI_COPY.stepProviderDescription}
          />
          {cloudProviders.length > 0 ? <p className={styles.muted}>{AI_COPY.groupCloud}</p> : null}
          <div className={styles.providerGrid} data-testid="ai-providers">
            {cloudProviders.map((item) => (
              <ProviderCard key={item.key} item={item} onChoose={chooseProvider} />
            ))}
          </div>
          {localProviders.length > 0 ? (
            <>
              <p className={styles.muted}>{AI_COPY.groupLocal}</p>
              <div className={styles.providerGrid} data-testid="ai-local-providers">
                {localProviders.map((item) => (
                  <ProviderCard key={item.key} item={item} onChoose={chooseProvider} />
                ))}
              </div>
            </>
          ) : null}
          {localBusy ? <p data-testid="ai-local-detecting">{AI_COPY.localDetecting}</p> : null}
          {localStatus.some((entry) => !entry.available) ? (
            <p className={styles.muted} data-testid="ai-local-none">
              {AI_COPY.localNone}
            </p>
          ) : null}
          {error ? <InlineError>{error}</InlineError> : null}
          <div className={styles.actions}>
            <Button variant="secondary" onClick={() => setStage('welcome')}>
              {AI_COPY.cancel}
            </Button>
          </div>
        </Card>
      ) : null}

      {stage === 'model' ? (
        <Card>
          <PageHeader title={AI_COPY.stepModelTitle} description={AI_COPY.stepModelDescription} />
          <p className={styles.status} data-testid="ai-provider-chosen">
            {provider?.display_name}
          </p>
          {modelsBusy ? <p data-testid="ai-models-loading">{AI_COPY.modelLoading}</p> : null}
          {!modelsBusy && models.length === 0 ? (
            <p data-testid="ai-models-empty">{AI_COPY.modelEmpty}</p>
          ) : null}
          <Field label={AI_COPY.modelChoose}>
            {() => (
              <div className={styles.modelList} data-testid="ai-models">
                {models.map((entry) => (
                  <label key={entry.key} className={styles.modelRow} data-testid={`ai-model-${entry.key}`}>
                    <input
                      type="radio"
                      name="ai-model"
                      value={entry.key}
                      checked={model === entry.key}
                      onChange={() => setModel(entry.key)}
                    />
                    <span>{entry.display_name}</span>
                  </label>
                ))}
              </div>
            )}
          </Field>
          {error ? <InlineError>{error}</InlineError> : null}
          <div className={styles.actions}>
            <Button
              data-testid="ai-model-next"
              disabled={model === '' || modelsBusy}
              onClick={() => {
                setError(null);
                setStage('credential');
              }}
            >
              {AI_COPY.next}
            </Button>
            <Button variant="secondary" onClick={() => setStage('provider')}>
              {AI_COPY.back}
            </Button>
          </div>
        </Card>
      ) : null}

      {stage === 'credential' || stage === 'connecting' ? (
        <CredentialForm
          submitting={stage === 'connecting'}
          error={error}
          selected={selectedLine}
          keyNeeded={keyNeeded}
          local={provider?.locality === 'local'}
          apiKey={apiKey}
          onKeyChange={setApiKey}
          onCancel={() => {
            setError(null);
            setStage('model');
          }}
          onSubmit={() => void connect()}
        />
      ) : null}

      {stage === 'success' ? (
        <Card>
          <div className={styles.success} data-testid="ai-ready">
            <p className={styles.successMark}>✓ {AI_COPY.successTitle}</p>
            <p data-testid="ai-ready-selected">
              {AI_COPY.selectedLabel}
              {status?.provider ?? provider?.display_name} · {status?.model ?? model}
            </p>
            <p>{AI_COPY.successBody}</p>
            <p className={styles.muted}>
              {AI_COPY.successExampleLabel}
              {AI_COPY.successExample}
            </p>
            <Button data-testid="ai-use" onClick={() => setStage('assistant')}>
              {AI_COPY.startUsing}
            </Button>
          </div>
        </Card>
      ) : null}

      {stage === 'assistant' ? (
        <AssistantView
          connected={status?.connected ?? false}
          onReconnect={() => setStage('provider')}
        />
      ) : null}

      <AdvancedDetails status={status} onClear={clearConnection} />
    </section>
  );
}

function ProviderCard({
  item,
  onChoose,
}: {
  item: CustomerProvider;
  onChoose: (item: CustomerProvider) => Promise<void>;
}) {
  return (
    <button
      type="button"
      data-testid={`ai-provider-${item.key}`}
      className={styles.providerCard}
      onClick={() => void onChoose(item)}
    >
      <strong>{item.display_name}</strong>
      <span className={styles.muted}>{item.description}</span>
    </button>
  );
}

function CredentialForm({
  submitting,
  error,
  selected,
  keyNeeded,
  local,
  apiKey,
  onKeyChange,
  onCancel,
  onSubmit,
}: {
  submitting: boolean;
  error: string | null;
  selected: string;
  keyNeeded: boolean;
  local: boolean;
  apiKey: string;
  onKeyChange: (value: string) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const [visible, setVisible] = useState(false);
  const label = local ? AI_COPY.tokenLabel : AI_COPY.keyLabel;
  return (
    <Card>
      <PageHeader
        title={AI_COPY.stepCredentialTitle}
        description={AI_COPY.stepCredentialDescription}
      />
      <p className={styles.status} data-testid="ai-selected">
        {AI_COPY.selectedLabel}
        {selected}
      </p>
      {keyNeeded ? (
        <Field label={label} hint={local ? AI_COPY.tokenHint : AI_COPY.keyHint}>
          {({ id, describedBy }) => (
            <div className={styles.keyRow}>
              <Input
                id={id}
                type={visible ? 'text' : 'password'}
                value={apiKey}
                aria-describedby={describedBy}
                autoComplete="off"
                spellCheck={false}
                data-testid="ai-api-key"
                onChange={(event) => onKeyChange(event.target.value)}
              />
              <Button
                variant="secondary"
                size="small"
                aria-label={visible ? AI_COPY.keyHide : AI_COPY.keyShow}
                onClick={() => setVisible((value) => !value)}
              >
                {visible ? AI_COPY.keyHide : AI_COPY.keyShow}
              </Button>
            </div>
          )}
        </Field>
      ) : null}
      {!local ? <p className={styles.muted}>{AI_COPY.keyHelp}</p> : null}
      {error ? <InlineError>{error}</InlineError> : null}
      <div className={styles.actions}>
        <Button data-testid="ai-enable" loading={submitting} onClick={onSubmit}>
          {local ? AI_COPY.enableLocal : AI_COPY.enable}
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={submitting}>
          {AI_COPY.back}
        </Button>
      </div>
      {submitting ? <p data-testid="ai-progress">{AI_COPY.connecting}</p> : null}
    </Card>
  );
}

function AssistantView({
  connected,
  onReconnect,
}: {
  connected: boolean;
  onReconnect: () => void;
}) {
  const { client } = useAuth();
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const asked = useRef(false);

  const ask = async () => {
    const text = question.trim();
    if (text.length === 0 || pending) {
      return;
    }
    setPending(true);
    setNotice(null);
    asked.current = true;
    try {
      const reply = await sendAIMessage(client, text);
      if (reply.status === 'COMPLETED') {
        const value =
          (reply.result as { reply?: unknown }).reply ?? (reply.result as { text?: unknown }).text;
        setAnswer(typeof value === 'string' && value.length > 0 ? value : AI_COPY.answerFallback);
      } else {
        setAnswer(null);
        setNotice(assistantErrorMessage(reply.failure_code));
      }
    } catch {
      setAnswer(null);
      setNotice(AI_COPY.assistantUnavailable);
    } finally {
      setPending(false);
      setQuestion('');
    }
  };

  return (
    <Card>
      <PageHeader title={AI_COPY.assistantTitle} description={AI_COPY.assistantDescription} />
      <p className={styles.status} data-testid="ai-status">
        {connected ? AI_COPY.statusConnected : AI_COPY.statusDisconnected}
      </p>
      {!connected ? (
        <div className={styles.actions} data-testid="ai-not-connected">
          <InlineError>{AI_COPY.expired}</InlineError>
          <Button onClick={onReconnect}>{AI_COPY.reconnect}</Button>
        </div>
      ) : null}
      {!asked.current ? (
        <div data-testid="ai-empty">
          <p>{AI_COPY.emptyTitle}</p>
          <p>{AI_COPY.emptyBody}</p>
          <p className={styles.muted}>{AI_COPY.emptyExample}</p>
        </div>
      ) : null}
      {asked.current ? <p data-testid="ai-greeting">{AI_COPY.assistantGreeting}</p> : null}
      {answer ? <p data-testid="ai-answer">{answer}</p> : null}
      {notice ? <InlineError>{notice}</InlineError> : null}
      <TextField
        label={AI_COPY.questionLabel}
        value={question}
        onChange={setQuestion}
        placeholder={AI_COPY.questionPlaceholder}
      />
      <div className={styles.actions}>
        <Button data-testid="ai-ask" loading={pending} onClick={() => void ask()} disabled={!connected}>
          {pending ? AI_COPY.sending : AI_COPY.send}
        </Button>
        <span className={styles.muted}>{AI_COPY.emptyExample}</span>
      </div>
    </Card>
  );
}

function AdvancedDetails({
  status,
  onClear,
}: {
  status: ConnectionStatus | null;
  onClear: () => Promise<void>;
}) {
  const [confirming, setConfirming] = useState(false);
  return (
    <details className={styles.advanced} data-testid="ai-advanced">
      <summary>{AI_COPY.advancedSummary}</summary>
      <ul className={styles.detailList}>
        <li>
          {AI_COPY.advancedProviderLabel}：
          {status?.connected
            ? (status.provider ?? AI_COPY.providerPrimary)
            : AI_COPY.advancedDisconnected}
        </li>
        <li>
          {AI_COPY.advancedModelLabel}：
          {status?.connected ? (status.model ?? '—') : AI_COPY.advancedDisconnected}
        </li>
        <li>
          {AI_COPY.advancedStatusLabel}：
          {status?.connected ? AI_COPY.advancedConnected : AI_COPY.advancedDisconnected}
        </li>
        <li>
          {AI_COPY.advancedSecurityLabel}：{AI_COPY.advancedSecurityOk}
        </li>
      </ul>
      <div className={styles.actions}>
        <Button variant="secondary" size="small" onClick={() => setConfirming(true)}>
          {AI_COPY.clearButton}
        </Button>
      </div>
      <Dialog
        open={confirming}
        title={AI_COPY.clearDialogTitle}
        description={AI_COPY.clearDialogBody}
        onClose={() => setConfirming(false)}
        footer={
          <div>
            <Button variant="secondary" onClick={() => setConfirming(false)}>
              {AI_COPY.cancel}
            </Button>{' '}
            <Button
              variant="danger"
              data-testid="ai-clear-confirm"
              onClick={() => {
                setConfirming(false);
                void onClear();
              }}
            >
              {AI_COPY.clearDialogConfirm}
            </Button>
          </div>
        }
      >
        <p>{AI_COPY.clearDialogBody}</p>
      </Dialog>
    </details>
  );
}
