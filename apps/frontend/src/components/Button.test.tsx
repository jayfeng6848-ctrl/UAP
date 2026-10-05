/** Button primitive tests (Appendix AL §34). */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Button } from './Button';

describe('Button', () => {
  it('renders a native button that defaults to type="button"', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Save</Button>);

    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toHaveAttribute('type', 'button');

    await user.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('is reachable by keyboard', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Confirm</Button>);

    await user.tab();
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('disables itself while loading and prevents a duplicate submit', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <Button loading onClick={onClick}>
        Save
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');

    await user.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('respects an explicit disabled state and submit type', () => {
    render(
      <Button type="submit" disabled>
        Submit
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Submit' });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('type', 'submit');
  });

  it('applies distinct classes per variant and size', () => {
    const { rerender } = render(<Button variant="primary">A</Button>);
    const primary = screen.getByRole('button', { name: 'A' }).className;

    rerender(
      <Button variant="danger" size="small">
        A
      </Button>,
    );
    const danger = screen.getByRole('button', { name: 'A' }).className;

    expect(primary).not.toBe(danger);
    expect(danger.split(/\s+/).length).toBeGreaterThan(1);
  });
});
