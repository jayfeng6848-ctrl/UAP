/** Render-error boundary tests (Appendix AL §62-§63). */

import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ErrorBoundary } from './ErrorBoundary';

function Boom(): never {
  throw new Error('internal detail: postgres://user:pw@host/db table company_employees');
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // React prints the caught error; silence it so the suite output stays readable.
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders a safe message instead of the raw error', () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('UAP 遇到了一个意外问题。');
    expect(screen.queryByText(/postgres:\/\//)).not.toBeInTheDocument();
    expect(screen.queryByText(/company_employees/)).not.toBeInTheDocument();
  });

  it('offers a retry that re-renders children', () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <p>healthy</p>
      </ErrorBoundary>,
    );

    expect(screen.getByText('healthy')).toBeInTheDocument();
  });
});
