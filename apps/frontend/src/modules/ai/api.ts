/** Typed AI onboarding API (HD-P21-17 · HD-P21-AI-01..04). Customer-safe codes only. */

import { ApiError } from '../../platform/api';
import type { ApiClient } from '../../platform/api';
import { AI_COPY } from './copy';

export type ProviderLocality = 'cloud' | 'local';
export type ProviderAuth = 'required' | 'optional' | 'none';

export interface CustomerProvider {
  key: string;
  display_name: string;
  description: string;
  locality: ProviderLocality;
  auth: ProviderAuth;
}

export interface ProviderModel {
  key: string;
  display_name: string;
}

export interface ProviderModels {
  provider: string;
  locality: ProviderLocality;
  models: ProviderModel[];
}

export interface LocalProviderStatus {
  key: string;
  display_name: string;
  description: string;
  auth: ProviderAuth;
  available: boolean;
  auth_required: boolean;
  models: string[];
  error: string | null;
}

export interface ConnectionStatus {
  connected: boolean;
  provider: string | null;
  /** HD-P21-AI-04: provider and model are two independent facts. */
  model: string | null;
  expires_at: number | null;
  assistant_ready: boolean;
  ttl_seconds: number;
  /** Customer-visible AI service list (names + one line), supplied by the backend. */
  providers?: CustomerProvider[];
}

export interface ConnectionResult {
  connected: boolean;
  provider: string;
  model: string;
  expires_at: number;
  ttl_seconds: number;
}

export interface AssistantReply {
  status: string;
  result: Record<string, unknown>;
  failure_code: string | null;
}

export function getConnection(client: ApiClient): Promise<ConnectionStatus> {
  return client.get<ConnectionStatus>('/ai/connection');
}

export function listProviders(client: ApiClient): Promise<{ providers: CustomerProvider[] }> {
  return client.get<{ providers: CustomerProvider[] }>('/ai/providers');
}

/** HD-P21-AI-04 §6/§7: the selectable models of one service. */
export function listProviderModels(
  client: ApiClient,
  providerKey: string,
): Promise<ProviderModels> {
  return client.get<ProviderModels>(`/ai/providers/${encodeURIComponent(providerKey)}/models`);
}

/** HD-P21-AI-02/§13: server-side detection of the local runtimes on the UAP host. */
export function detectLocalProviders(
  client: ApiClient,
): Promise<{ providers: LocalProviderStatus[] }> {
  return client.get<{ providers: LocalProviderStatus[] }>('/ai/local/providers');
}

export function connectAI(
  client: ApiClient,
  provider: string,
  model: string,
  apiKey = '',
): Promise<ConnectionResult> {
  const body: Record<string, string> = { provider, model };
  if (apiKey) {
    body.api_key = apiKey;
  }
  return client.post<ConnectionResult>('/ai/connection', body);
}

export function disconnectAI(client: ApiClient): Promise<{ cleared: boolean }> {
  return client.request<{ cleared: boolean }>('DELETE', '/ai/connection');
}

export function sendAIMessage(client: ApiClient, text: string): Promise<AssistantReply> {
  return client.post<AssistantReply>('/ai/messages', { text });
}

/** Customer language (HD-P21-18 §9). Technical detail never reaches the customer. */
export function connectErrorMessage(error: unknown): string {
  const code = error instanceof ApiError ? error.detail : null;
  switch (code) {
    case 'api_key_rejected':
      return AI_COPY.errorInvalidKey;
    case 'api_key_required':
      return AI_COPY.errorKeyRequired;
    case 'ai_service_unreachable':
      return AI_COPY.errorNetwork;
    case 'model_not_available':
      return AI_COPY.errorModelUnavailable;
    case 'local_auth_required':
      return AI_COPY.errorLocalAuthRequired;
    case 'local_model_not_found':
      return AI_COPY.errorLocalModelMissing;
    case 'local_service_unreachable':
      return AI_COPY.errorLocalUnavailable;
    case 'local_protocol_error':
      return AI_COPY.errorLocalProtocol;
    case 'ai_not_configured':
    case 'provider_not_supported':
      return AI_COPY.errorConfig;
    default:
      return AI_COPY.errorConfig;
  }
}

export function assistantErrorMessage(failureCode: string | null): string {
  if (failureCode === 'CREDENTIAL_UNAVAILABLE') {
    return AI_COPY.expired;
  }
  if (failureCode === 'AUTHORIZATION_DENIED' || failureCode === 'PERMISSION_DENIED') {
    return AI_COPY.authorizationDenied;
  }
  if (failureCode === 'MODEL_UNAVAILABLE' || failureCode === 'MODEL_PROVIDER_MISMATCH') {
    return AI_COPY.errorModelUnavailable;
  }
  if (failureCode === 'LOCAL_AI_UNAVAILABLE' || failureCode === 'LOCAL_MODEL_NOT_FOUND') {
    return AI_COPY.errorLocalUnavailable;
  }
  return AI_COPY.assistantUnavailable;
}
