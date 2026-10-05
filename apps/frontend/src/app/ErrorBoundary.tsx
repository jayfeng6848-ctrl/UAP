/**
 * Render-error boundary (Appendix AL H62/H63).
 *
 * The user sees a safe message and, when available, a correlation reference — never
 * a stack trace, component internals, API URL or database detail.
 */

import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

import { GlobalError } from '../platform/feedback/states';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // No console output of the raw error: it may contain sensitive content.
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      return (
        <GlobalError
          message="The console hit an unexpected error."
          onRetry={() => {
            this.setState({ hasError: false });
          }}
        />
      );
    }
    return this.props.children;
  }
}
