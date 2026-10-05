/**
 * Sign-in page (Appendix AL H04/H15 · HD-P21-06 device correction).
 *
 * Reuses the existing platform session endpoint. A session token is issued by the
 * backend only for a verified device, so the form collects the account, the
 * password and the id of a device that is **already enrolled**. The page never
 * enrolls a device, never trusts one, never fabricates a session and never stores
 * credentials or tokens in browser storage (the token stays memory-only inside
 * AuthProvider).
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { Button, Card, Field, Input, PageHeader, TextField } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { InlineError } from '../../../platform/feedback/states';

interface LoginLocationState {
  from?: string;
}

/** Explains what the Device ID is without exposing it as a developer flag. */
const DEVICE_HINT =
  'The id of the device already enrolled for this account. The platform issues a session only for a verified device.';

export function LoginPage() {
  const { login, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched] = useState(false);

  const trimmedLogin = loginId.trim();
  const trimmedDevice = deviceId.trim();

  const loginError = touched && trimmedLogin.length === 0 ? 'Login is required.' : undefined;
  const passwordError = touched && password.length === 0 ? 'Password is required.' : undefined;
  const deviceError =
    touched && trimmedDevice.length === 0 ? 'Device ID is required.' : undefined;

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice(null);
    setTouched(true);
    if (trimmedLogin.length === 0 || password.length === 0 || trimmedDevice.length === 0) {
      // Field-level validation: no half-complete session attempt is sent.
      return;
    }
    setSubmitting(true);
    const outcome = await login(trimmedLogin, password, trimmedDevice);
    setSubmitting(false);
    if (outcome === 'authenticated') {
      const state = location.state as LoginLocationState | null;
      navigate(state?.from ?? '/', { replace: true });
      return;
    }
    if (outcome === 'device_required') {
      setNotice(
        'Credentials verified, but this device is not enrolled: the platform issues a session only for a verified device. Enrolling a device is a separate step and never happens on this page.',
      );
      return;
    }
    setNotice('Sign-in failed. Check the account, the password and the device id, then try again.');
  };

  return (
    <Card>
      <PageHeader
        title="Sign in to UAP Console"
        description="Platform identity, password and the enrolled device this session is bound to."
      />
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <TextField label="Login" value={loginId} onChange={setLoginId} error={loginError} />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          error={passwordError}
        />
        <Field label="Device ID" error={deviceError} hint={DEVICE_HINT}>
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              type="text"
              value={deviceId}
              invalid={invalid}
              aria-describedby={describedBy}
              autoComplete="off"
              spellCheck={false}
              onChange={(event) => setDeviceId(event.target.value)}
            />
          )}
        </Field>
        <Button type="submit" loading={submitting}>
          Sign in
        </Button>
      </form>
      {notice ? <InlineError>{notice}</InlineError> : null}
      {error?.detail ? <InlineError>{error.detail}</InlineError> : null}
    </Card>
  );
}
