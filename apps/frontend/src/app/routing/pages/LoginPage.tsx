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
const DEVICE_HINT = '这是已经为该账号注册的设备 ID。只有在已验证的设备上才会建立会话。';

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

  const loginError = touched && trimmedLogin.length === 0 ? '请输入账号。' : undefined;
  const passwordError = touched && password.length === 0 ? '请输入密码。' : undefined;
  const deviceError =
    touched && trimmedDevice.length === 0 ? '请输入设备 ID。' : undefined;

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
        '凭据已验证，但这台设备尚未注册：只有在已验证的设备上才会建立会话。设备注册是单独的步骤，不会在这个页面完成。',
      );
      return;
    }
    setNotice('登录失败。请检查账号、密码和设备 ID，然后重试。');
  };

  return (
    <Card>
      <PageHeader
        title="登录 UAP"
        description="使用账号、密码和已注册的设备登录。"
      />
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <TextField label="账号" value={loginId} onChange={setLoginId} error={loginError} />
        <TextField
          label="密码"
          type="password"
          value={password}
          onChange={setPassword}
          error={passwordError}
        />
        <Field label="设备 ID" error={deviceError} hint={DEVICE_HINT}>
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
          登录
        </Button>
      </form>
      {notice ? <InlineError>{notice}</InlineError> : null}
      {error?.detail ? <InlineError>{error.detail}</InlineError> : null}
    </Card>
  );
}
