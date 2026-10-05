/**
 * Permission-UX boundary tests (Appendix AL §40-§41).
 *
 * There is no frontend ACL engine: permission data is unavailable, hints may only
 * affect presentation, and the backend stays the decision point.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CapabilityHint, capabilityAvailability } from './capability';

describe('capabilityAvailability', () => {
  it('reports permission data as unknown rather than guessing', () => {
    expect(capabilityAvailability()).toBe('unknown');
  });
});

describe('CapabilityHint', () => {
  it('renders children while availability is unknown (fail-open for UX only)', () => {
    render(
      <CapabilityHint>
        <button type="button">Suspend employee</button>
      </CapabilityHint>,
    );

    expect(screen.getByRole('button', { name: 'Suspend employee' })).toBeInTheDocument();
  });

  it('may hide children when the platform says the capability is unavailable', () => {
    render(
      <CapabilityHint availability="unavailable">
        <button type="button">Suspend employee</button>
      </CapabilityHint>,
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
