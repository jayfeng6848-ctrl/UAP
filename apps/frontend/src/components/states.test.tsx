/** Shared presentation-state and status tests (Appendix AL §33, §39). */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Badge } from './Badge';
import { Card } from './Card';
import { PageHeader } from './PageHeader';
import { EmptyState, ErrorState, LoadingState } from './states';

describe('EmptyState', () => {
  it('renders a title and optional description', () => {
    render(<EmptyState title="No employees" description="Invite someone to begin." />);

    expect(screen.getByRole('heading', { name: 'No employees' })).toBeInTheDocument();
    expect(screen.getByText('Invite someone to begin.')).toBeInTheDocument();
  });
});

describe('LoadingState', () => {
  it('announces progress through a live region', () => {
    render(<LoadingState />);

    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent('Loading…');
  });
});

describe('ErrorState', () => {
  it('is an alert and shows a correlation reference when available', () => {
    render(<ErrorState message="Could not load employees." correlationId="corr-42" />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Could not load employees.');
    expect(screen.getByText(/corr-42/)).toBeInTheDocument();
  });

  it('renders recovery actions when supplied', () => {
    render(<ErrorState message="Failed" actions={<button type="button">Retry</button>} />);

    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });
});

describe('Badge', () => {
  it('communicates status with text, never colour alone', () => {
    render(<Badge tone="danger">Suspended</Badge>);

    expect(screen.getByText('Suspended')).toBeInTheDocument();
  });
});

describe('Card / PageHeader', () => {
  it('renders a titled page header with content', () => {
    render(
      <Card>
        <PageHeader title="Overview" description="Platform foundation" />
      </Card>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByText('Platform foundation')).toBeInTheDocument();
  });
});
