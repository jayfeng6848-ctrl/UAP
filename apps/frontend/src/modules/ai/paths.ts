/** AI module path helpers (HD-P21-17). The URL is the tenant authority. */

const base = (tenantId: string) => `/tenants/${encodeURIComponent(tenantId)}/ai`;

export const AI_ENTRY_PATH = '/ai';

export const aiPaths = {
  home: (tenantId: string) => base(tenantId),
  assistant: (tenantId: string) => `${base(tenantId)}/assistant`,
} as const;
