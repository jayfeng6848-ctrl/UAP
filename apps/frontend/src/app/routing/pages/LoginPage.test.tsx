/**
 * Login page tests for the HD-P21-06 device correction.
 *
 * They pin the correction's contract: the form exposes an ordinary Device ID
 * input, forwards it to the existing `AuthProvider.login(login, password,
 * device_id)` path, keeps the backend's error semantics, stores nothing and
 * never authenticates without a server-issued token.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../../platform/api';
import type { ApiClient, MeResponse } from '../../../platform/api';
import { AuthProvider } from '../../../platform/auth/AuthContext';
import { LoginPage } from './LoginPage';

const DEVICE_ID = '0199aaaa-bbbb-7ccc-8ddd-eeeeffff0000';

function meResponse(): MeResponse {
  return {
    correlation_id: 'corr',
    session_id: 'sess-1',
    device_id: DEVICE_ID,
    identity_id: 'ident-1',
    user_id: 'user-1',
    tenant_id: 'tenant-1',
    space_id: null,
    subject_type: 'user',
    scope: 'TENANT',
    authentication_assurance: 'session_verified',
  };
}

interface StubClient {
  client: ApiClient;
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
}

function makeStubClient(): StubClient {
  const get = vi.fn();
  const post = vi.fn();
  const patch = vi.fn();
  const request = vi.fn();
  return { client: { get, post, patch, request } as unknown as ApiClient, get, post };
}

function renderLogin(client: ApiClient) {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider client={client}>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  );
}

async function fillForm(deviceId: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Login'), 'ada@example.invalid');
  await user.type(screen.getByLabelText('Password'), 'correct-horse');
  if (deviceId.length > 0) {
    await user.type(screen.getByLabelText('Device ID'), deviceId);
  }
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
}

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe('LoginPage — device correction (P21-RUT-03)', () => {
  it('exposes an ordinary Device ID input next to account and password', () => {
    renderLogin(makeStubClient().client);

    expect(screen.getByLabelText('Login')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
    const device = screen.getByLabelText('Device ID');
    expect(device).toBeInTheDocument();
    expect(device).toHaveAttribute('type', 'text');
    expect(screen.getByText(/already enrolled for this account/i)).toBeInTheDocument();
  });

  it('passes the entered Device ID into the existing session request', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(meResponse());
    renderLogin(stub.client);

    await fillForm(DEVICE_ID);

    await waitFor(() =>
      expect(stub.post).toHaveBeenCalledWith('/sessions', {
        login: 'ada@example.invalid',
        password: 'correct-horse',
        device_id: DEVICE_ID,
      }),
    );
  });

  it('blocks submission and explains why when the Device ID is empty', async () => {
    const stub = makeStubClient();
    renderLogin(stub.client);

    await fillForm('');

    expect(await screen.findByText('Device ID is required.')).toBeInTheDocument();
    expect(stub.post).not.toHaveBeenCalled();
  });

  it('keeps the backend device semantics instead of reporting a bad password', async () => {
    const stub = makeStubClient();
    // The frozen contract: credentials verified, but no session is issued for an
    // unregistered device.
    stub.post.mockResolvedValueOnce({
      user_id: 'user-1',
      identity_id: 'ident-1',
      authentication_assurance: 'credential_verified',
    });
    renderLogin(stub.client);

    await fillForm('00000000-0000-7000-8000-000000000000');

    expect(await screen.findByText(/this device is not enrolled/i)).toBeInTheDocument();
    expect(screen.queryByText(/sign-in failed/i)).not.toBeInTheDocument();
    expect(stub.get).not.toHaveBeenCalled();
  });

  it('reaches the existing authenticated session flow with a valid device', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(meResponse());
    renderLogin(stub.client);

    await fillForm(DEVICE_ID);

    await waitFor(() => expect(stub.get).toHaveBeenCalledWith('/me'));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('keeps the token memory-only', async () => {
    const stub = makeStubClient();
    stub.post.mockResolvedValueOnce({ token: 'memory-token', user_id: 'user-1' });
    stub.get.mockResolvedValueOnce(meResponse());
    renderLogin(stub.client);

    await fillForm(DEVICE_ID);
    await waitFor(() => expect(stub.get).toHaveBeenCalledWith('/me'));

    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
    expect(document.cookie).toBe('');
  });

  it('never authenticates without a server-issued token (no auth bypass)', async () => {
    const stub = makeStubClient();
    stub.post.mockRejectedValueOnce(
      new ApiError({
        status: 401,
        code: 'AUTH_REQUIRED',
        message: 'authentication failed',
        correlationId: 'c-1',
        detail: 'authentication failed',
      }),
    );
    renderLogin(stub.client);

    await fillForm(DEVICE_ID);

    expect(await screen.findByText(/sign-in failed/i)).toBeInTheDocument();
    expect(stub.get).not.toHaveBeenCalled();
  });
});
