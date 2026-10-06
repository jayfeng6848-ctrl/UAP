/**
 * Customer AI journey — universal provider + model selection (HD-P21-AI-04 §18,
 * Implementation Authorization §22 items 30–33).
 *
 * The production composition is exercised: AuthProvider (injected client) →
 * FeedbackProvider → the real page. Only the HTTP client is a double.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { ApiError } from '../../../platform/api';
import { AuthProvider } from '../../../platform/auth/AuthContext';
import { FeedbackProvider } from '../../../platform/feedback/FeedbackProvider';
import { makeStubClient } from '../../../test/companyHarness';
import type { RecordedCall } from '../../../test/companyHarness';
import { AIHomePage } from './AIHomePage';

const TENANT = '3f1a2b4c-5d6e-4f70-8192-a3b4c5d6e7f8';

const CLOUD = {
  key: 'deepseek',
  display_name: 'DeepSeek',
  description: '适合中文对话、分析与工作助手',
  locality: 'cloud',
  auth: 'required',
};
const LOCAL = {
  key: 'ollama-local',
  display_name: 'Ollama（本机）',
  description: '使用这台电脑上已经安装的 Ollama',
  locality: 'local',
  auth: 'none',
};

function renderAI(handler: (call: RecordedCall) => unknown) {
  const stub = makeStubClient(handler);
  render(
    <FeedbackProvider>
      <AuthProvider client={stub.client}>
        <AIHomePage tenantId={TENANT} />
      </AuthProvider>
    </FeedbackProvider>,
  );
  return stub;
}

const base = (call: RecordedCall): unknown => {
  if (call.path === '/ai/connection' && call.method === 'GET') {
    return {
      connected: false,
      provider: null,
      model: null,
      expires_at: null,
      assistant_ready: true,
      ttl_seconds: 1800,
    };
  }
  if (call.path === '/ai/providers') {
    return { providers: [CLOUD, LOCAL] };
  }
  if (call.path === '/ai/providers/deepseek/models') {
    return {
      provider: 'deepseek',
      locality: 'cloud',
      models: [
        { key: 'deepseek-chat', display_name: 'DeepSeek Chat' },
        { key: 'deepseek-reasoner', display_name: 'DeepSeek Reasoner' },
      ],
    };
  }
  if (call.path === '/ai/local/providers') {
    return {
      providers: [
        {
          key: 'ollama-local',
          display_name: 'Ollama（本机）',
          description: '使用这台电脑上已经安装的 Ollama',
          auth: 'none',
          available: true,
          auth_required: false,
          models: ['qwen3:8b'],
          error: null,
        },
      ],
    };
  }
  if (call.path === '/ai/providers/ollama-local/models') {
    return {
      provider: 'ollama-local',
      locality: 'local',
      models: [{ key: 'qwen3:8b', display_name: 'qwen3:8b' }],
    };
  }
  if (call.path === '/ai/connection' && call.method === 'POST') {
    const body = call.body as { provider: string; model: string };
    return {
      connected: true,
      provider: body.provider,
      model: body.model,
      expires_at: 1,
      ttl_seconds: 1800,
    };
  }
  return {};
};

describe('AIHomePage — universal model selection', () => {
  it('runs the frozen 服务 → 模型 → 凭证 → 启用 journey and shows the selection', async () => {
    const user = userEvent.setup();
    const stub = renderAI(base);

    await user.click(await screen.findByTestId('ai-start'));
    await user.click(await screen.findByTestId('ai-provider-deepseek'));

    expect(await screen.findByTestId('ai-models')).toBeInTheDocument();
    // §18: the customer must pick a model — the step cannot be skipped.
    expect(screen.getByTestId('ai-model-next')).toBeDisabled();
    await user.click(screen.getByTestId('ai-model-deepseek-chat'));
    await user.click(screen.getByTestId('ai-model-next'));

    expect(await screen.findByTestId('ai-selected')).toHaveTextContent('DeepSeek');
    await user.type(screen.getByTestId('ai-api-key'), 'sk-test-key-123456');
    await user.click(screen.getByTestId('ai-enable'));

    expect(await screen.findByTestId('ai-ready-selected')).toHaveTextContent('deepseek-chat');
    const posted = stub.callsTo('POST', '/ai/connection').at(-1);
    expect(posted?.body).toEqual({
      provider: 'deepseek',
      model: 'deepseek-chat',
      api_key: 'sk-test-key-123456',
    });
  });

  it('shows the customer-language model list and never leaks technical concepts', async () => {
    const user = userEvent.setup();
    renderAI(base);

    await user.click(await screen.findByTestId('ai-start'));
    await user.click(await screen.findByTestId('ai-provider-deepseek'));

    expect(await screen.findByTestId('ai-models')).toBeInTheDocument();
    expect(screen.getByTestId('ai-provider-chosen')).toHaveTextContent('DeepSeek');
    const body = document.body.textContent ?? '';
    expect(body).not.toMatch(/http:\/\/|https:\/\/|adapter|protocol|secret_ref|ai_route/i);
  });

  it('connects a local service without any credential and uses discovered models', async () => {
    const user = userEvent.setup();
    const stub = renderAI(base);

    await user.click(await screen.findByTestId('ai-start'));
    await user.click(await screen.findByTestId('ai-provider-ollama-local'));

    expect(await screen.findByTestId('ai-model-qwen3:8b')).toBeInTheDocument();
    await user.click(screen.getByTestId('ai-model-qwen3:8b'));
    await user.click(screen.getByTestId('ai-model-next'));

    // §13/§11: no key field for a credential-free local runtime.
    expect(screen.queryByTestId('ai-api-key')).not.toBeInTheDocument();
    await user.click(screen.getByTestId('ai-enable'));

    expect(await screen.findByTestId('ai-ready-selected')).toHaveTextContent('qwen3:8b');
    const posted = stub.callsTo('POST', '/ai/connection').at(-1);
    expect(posted?.body).toEqual({ provider: 'ollama-local', model: 'qwen3:8b' });
  });

  it('reports an absent local runtime in customer language and stays on the service step', async () => {
    const user = userEvent.setup();
    renderAI((call) => {
      if (call.path === '/ai/local/providers') {
        return {
          providers: [
            {
              key: 'ollama-local',
              display_name: 'Ollama（本机）',
              description: '使用这台电脑上已经安装的 Ollama',
              auth: 'none',
              available: false,
              auth_required: false,
              models: [],
              error: 'LOCAL_AI_UNAVAILABLE',
            },
          ],
        };
      }
      return base(call);
    });

    await user.click(await screen.findByTestId('ai-start'));
    await user.click(await screen.findByTestId('ai-provider-ollama-local'));

    expect(await screen.findByTestId('ai-local-none')).toHaveTextContent('未检测到本地 AI');
    expect(screen.queryByTestId('ai-models')).not.toBeInTheDocument();
  });

  it('maps a rejected model to a customer-readable message without internals', async () => {
    const user = userEvent.setup();
    renderAI((call) => {
      if (call.path === '/ai/connection' && call.method === 'POST') {
        return new ApiError({
          status: 400,
          code: 'VALIDATION_OR_NOT_FOUND',
          message: 'model_not_available',
          detail: 'model_not_available',
          correlationId: 'c-model',
        });
      }
      return base(call);
    });

    await user.click(await screen.findByTestId('ai-start'));
    await user.click(await screen.findByTestId('ai-provider-deepseek'));
    await user.click(await screen.findByTestId('ai-model-deepseek-chat'));
    await user.click(screen.getByTestId('ai-model-next'));
    await user.type(screen.getByTestId('ai-api-key'), 'sk-test-key-123456');
    await user.click(screen.getByTestId('ai-enable'));

    await waitFor(() => expect(document.body.textContent ?? '').toContain('这个模型当前不可用'));
    expect(document.body.textContent ?? '').not.toMatch(/sql|constraint|traceback/i);
  });
});
