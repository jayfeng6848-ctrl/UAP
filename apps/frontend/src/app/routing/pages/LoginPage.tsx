/**
 * Sign-in page (Appendix AL H04/H15).
 *
 * Reuses the existing platform session endpoint. A session token is issued by the
 * backend only for a verified device — this page never fabricates a session and
 * never stores credentials in browser storage.
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { Button, Card, PageHeader, TextField } from '../../../components';
import { useAuth } from '../../../platform/auth/AuthContext';
import { InlineError } from '../../../platform/feedback/states';

interface LoginLocationState {
  from?: string;
}

export function LoginPage() {
  const { login, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice(null);
    setSubmitting(true);
    const outcome = await login(loginId, password);
    setSubmitting(false);
    if (outcome === 'authenticated') {
      const state = location.state as LoginLocationState | null;
      navigate(state?.from ?? '/', { replace: true });
      return;
    }
    if (outcome === 'device_required') {
      setNotice(
        'Credentials verified, but this device is not enrolled: the platform issues a session only for a verified device.',
      );
      return;
    }
    setNotice('Sign-in failed. Check your credentials and try again.');
  };

  return (
    <Card>
      <PageHeader title="Sign in to UAP Console" description="Platform identity and session." />
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <TextField label="Login" value={loginId} onChange={setLoginId} />
        <TextField label="Password" type="password" value={password} onChange={setPassword} />
        <Button type="submit" loading={submitting}>
          Sign in
        </Button>
      </form>
      {notice ? <InlineError>{notice}</InlineError> : null}
      {error?.detail ? <InlineError>{error.detail}</InlineError> : null}
    </Card>
  );
}
