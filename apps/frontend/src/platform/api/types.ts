/**
 * Wire types for the endpoints the Foundation consumes.
 *
 * Only fields that the backend actually returns are modelled. `/me` returns the
 * frozen log-safe context (never a complete permission set).
 */

export interface MetaResponse {
  name: string;
  version: string;
  env: string;
  phase: string;
  core_modules: string[];
  domains: Array<Record<string, unknown>>;
}

/** `GET /me` — see services/context/model.py::LOG_SAFE_FIELDS. */
export interface MeResponse {
  correlation_id: string | null;
  session_id: string | null;
  device_id: string | null;
  identity_id: string | null;
  user_id: string | null;
  tenant_id: string | null;
  space_id: string | null;
  subject_type: string | null;
  scope: string | null;
  authentication_assurance: string | null;
}

/** `POST /sessions` — a token is issued only when a verified device is supplied. */
export interface LoginResponse {
  user_id: string;
  identity_id: string;
  authentication_assurance: string;
  session_id?: string;
  token?: string;
  device_id?: string;
  expires_at?: string;
  absolute_expires_at?: string;
}

export interface RefreshResponse {
  session_id: string;
  expires_at: string;
  absolute_expires_at: string | null;
}

export interface LogoutResponse {
  revoked: number;
}
