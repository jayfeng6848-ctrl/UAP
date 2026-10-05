/**
 * Global feedback layer (Appendix AL H17/H30).
 *
 * One place owns toasts and their live-region semantics so no page invents its own
 * notification stack. Messages are always human-readable: internal exceptions,
 * stack traces, SQL and credentials never reach the DOM.
 */

import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type ToastTone = 'info' | 'success' | 'error';

export interface Toast {
  id: string;
  tone: ToastTone;
  message: string;
}

export interface FeedbackContextValue {
  toasts: Toast[];
  notify: (message: string, tone?: ToastTone) => void;
  dismiss: (id: string) => void;
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null);

let toastSequence = 0;

export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback((message: string, tone: ToastTone = 'info') => {
    toastSequence += 1;
    setToasts((current) => [...current, { id: `toast-${toastSequence}`, tone, message }]);
  }, []);

  const value = useMemo<FeedbackContextValue>(
    () => ({ toasts, notify, dismiss }),
    [toasts, notify, dismiss],
  );

  return (
    <FeedbackContext.Provider value={value}>
      {children}
      <div role="status" aria-live="polite" data-testid="uap-toast-region">
        {toasts.map((toast) => (
          <div key={toast.id} data-tone={toast.tone}>
            <span>{toast.message}</span>
            <button type="button" onClick={() => dismiss(toast.id)}>
              Dismiss
            </button>
          </div>
        ))}
      </div>
    </FeedbackContext.Provider>
  );
}

export function useFeedback(): FeedbackContextValue {
  const context = useContext(FeedbackContext);
  if (context === null) {
    throw new Error('useFeedback must be used inside FeedbackProvider');
  }
  return context;
}
