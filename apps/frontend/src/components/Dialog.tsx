import { useEffect, useId, useRef } from 'react';
import type { ReactNode } from 'react';

import styles from './Dialog.module.css';

export interface DialogProps {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children?: ReactNode;
  footer?: ReactNode;
}

/** Elements that can hold keyboard focus, mirroring the browser's tabbable set. */
const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

function isUsable(element: HTMLElement): boolean {
  if (element.hasAttribute('disabled')) {
    return false;
  }
  if (element.hidden || element.closest('[inert]') !== null) {
    return false;
  }
  if (element.closest('[aria-hidden="true"]') !== null) {
    return false;
  }
  const style = globalThis.getComputedStyle?.(element);
  if (style && (style.display === 'none' || style.visibility === 'hidden')) {
    return false;
  }
  return true;
}

function focusableElements(root: HTMLElement): HTMLElement[] {
  const candidates = Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
  return candidates.filter((element) => element.tabIndex >= 0 && isUsable(element));
}

/**
 * Minimal, accessible dialog primitive: role/aria wiring, Escape to dismiss,
 * initial focus, focus containment while open and focus restoration on close.
 * Company flows will compose it later.
 *
 * Focus contract (F-P21-ACC-01):
 *   open  → remember the trigger, move focus to the first focusable control
 *           (or the dialog surface when the dialog holds no control)
 *   Tab   → cycle inside the dialog (last → first)
 *   Shift+Tab → cycle inside the dialog (first → last)
 *   close → return focus to the trigger, unless it is gone/unusable
 */
export function Dialog({ open, title, description, onClose, children, footer }: DialogProps) {
  const titleId = useId();
  const descriptionId = useId();
  const surfaceRef = useRef<HTMLDivElement | null>(null);
  /** Latest handler, so the focus effect depends only on `open`. */
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const surface = surfaceRef.current;
    // Only a real element of this document may be restored: never a stale or
    // detached reference, never <body>/<html> (that would be the ACC-01 defect).
    const restoreTarget =
      document.activeElement instanceof HTMLElement &&
      document.activeElement !== document.body &&
      document.activeElement !== document.documentElement
        ? document.activeElement
        : null;

    const initial = surface === null ? null : focusableElements(surface)[0] ?? surface;
    initial?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onCloseRef.current();
        return;
      }
      if (event.key !== 'Tab') {
        return;
      }
      const dialogSurface = surfaceRef.current;
      if (dialogSurface === null) {
        return;
      }
      const candidates = focusableElements(dialogSurface);
      if (candidates.length === 0) {
        // No control to cycle through: keep focus on the dialog surface itself.
        event.preventDefault();
        dialogSurface.focus();
        return;
      }
      const first = candidates[0];
      const last = candidates[candidates.length - 1];
      const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      if (active === null || active === dialogSurface || !dialogSurface.contains(active)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
        return;
      }
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
        return;
      }
      if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown, true);
    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      // Exactly one restoration per close; a missing/unusable trigger is not an error.
      if (restoreTarget !== null && restoreTarget.isConnected && isUsable(restoreTarget)) {
        restoreTarget.focus();
      }
    };
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className={styles.backdrop} data-testid="uap-dialog-backdrop">
      <div
        ref={surfaceRef}
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
      >
        <h2 id={titleId}>{title}</h2>
        {description ? <p id={descriptionId}>{description}</p> : null}
        <div>{children}</div>
        {footer ? <div>{footer}</div> : null}
      </div>
    </div>
  );
}
