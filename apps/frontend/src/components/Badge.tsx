import type { ReactNode } from 'react';

import styles from './Badge.module.css';

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger';

/** Status is communicated by text plus tone — never by colour alone. */
export function Badge({ tone = 'neutral', children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span className={[styles.badge, tone === 'neutral' ? null : styles[tone]].filter(Boolean).join(' ')}>
      {children}
    </span>
  );
}
