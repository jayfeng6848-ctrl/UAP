/**
 * Dialog primitive tests (Appendix AL §36/§39 · F-P21-ACC-01).
 *
 * Covers semantics (role/aria), initial focus, focus containment (Tab / Shift+Tab)
 * and focus restoration on close, including the degraded cases (no focusable
 * control, trigger removed).
 */

import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Dialog } from './Dialog';

/**
 * Trigger + dialog + outside controls: the exact shape behind the ACC-01 defect
 * (an "outside after" control used to steal focus on Tab).
 */
function Harness({
  removeTriggerOnOpen = false,
  withControls = true,
}: {
  removeTriggerOnOpen?: boolean;
  withControls?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [triggerGone, setTriggerGone] = useState(false);
  const showTrigger = !triggerGone;
  return (
    <div>
      <button type="button">outside before</button>
      {showTrigger ? (
        <button
          type="button"
          onClick={() => {
            if (removeTriggerOnOpen) {
              setTriggerGone(true);
            }
            setOpen(true);
          }}
        >
          open dialog
        </button>
      ) : null}
      <Dialog
        open={open}
        title="Confirm suspension"
        description="This stops access."
        onClose={() => setOpen(false)}
      >
        {withControls ? (
          <>
            <button type="button" onClick={() => setOpen(false)}>
              close dialog
            </button>
            <button type="button">cancel</button>
            <button type="button">confirm</button>
          </>
        ) : null}
      </Dialog>
      <button type="button">outside after</button>
    </div>
  );
}

async function openDialog(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'open dialog' }));
  return screen.getByRole('dialog', { name: 'Confirm suspension' });
}

describe('Dialog semantics', () => {
  it('renders nothing while closed', () => {
    render(
      <Dialog open={false} title="Confirm" onClose={() => undefined}>
        body
      </Dialog>,
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('exposes dialog semantics with an accessible name and description', () => {
    render(
      <Dialog open title="Confirm suspension" description="This stops access." onClose={() => undefined}>
        body
      </Dialog>,
    );

    const dialog = screen.getByRole('dialog', { name: 'Confirm suspension' });
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAccessibleDescription('This stops access.');
  });

  it('omits aria-describedby when there is no description', () => {
    render(
      <Dialog open title="Confirm" onClose={() => undefined}>
        body
      </Dialog>,
    );

    expect(screen.getByRole('dialog')).not.toHaveAttribute('aria-describedby');
  });

  it('closes on Escape', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <Dialog open title="Confirm" onClose={onClose}>
        body
      </Dialog>,
    );

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('stops listening to Escape once closed', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(
      <Dialog open title="Confirm" onClose={onClose}>
        body
      </Dialog>,
    );

    rerender(
      <Dialog open={false} title="Confirm" onClose={onClose}>
        body
      </Dialog>,
    );
    await user.keyboard('{Escape}');

    expect(onClose).not.toHaveBeenCalled();
  });
});

describe('Dialog initial focus', () => {
  it('focuses the first control inside the dialog on open', async () => {
    const user = userEvent.setup();
    render(<Harness />);

    const dialog = await openDialog(user);

    expect(dialog).toContainElement(document.activeElement as HTMLElement);
    expect(screen.getByRole('button', { name: 'close dialog' })).toHaveFocus();
  });

  it('focuses the dialog surface when the dialog holds no focusable control', async () => {
    const user = userEvent.setup();
    render(<Harness withControls={false} />);

    const dialog = await openDialog(user);

    expect(dialog).toHaveFocus();
  });
});

describe('Dialog focus containment (F-P21-ACC-01A)', () => {
  it('cycles forward from the last control to the first', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await openDialog(user);
    screen.getByRole('button', { name: 'confirm' }).focus();

    await user.tab();

    expect(screen.getByRole('button', { name: 'close dialog' })).toHaveFocus();
  });

  it('cycles backward from the first control to the last', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await openDialog(user);
    screen.getByRole('button', { name: 'close dialog' }).focus();

    await user.tab({ shift: true });

    expect(screen.getByRole('button', { name: 'confirm' })).toHaveFocus();
  });

  it('never leaves the dialog while tabbing repeatedly', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const dialog = await openDialog(user);

    for (let step = 0; step < 8; step += 1) {
      await user.tab();
      expect(dialog).toContainElement(document.activeElement as HTMLElement);
      expect(document.activeElement).not.toBe(document.body);
    }
    for (let step = 0; step < 8; step += 1) {
      await user.tab({ shift: true });
      expect(dialog).toContainElement(document.activeElement as HTMLElement);
    }
  });

  it('pulls focus back inside when a Tab starts from the dialog surface', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const dialog = await openDialog(user);
    dialog.focus();

    await user.tab();

    expect(dialog).toContainElement(document.activeElement as HTMLElement);
  });

  it('keeps focus on the surface when there is nothing to cycle through', async () => {
    const user = userEvent.setup();
    render(<Harness withControls={false} />);
    const dialog = await openDialog(user);

    await user.tab();

    expect(dialog).toHaveFocus();
  });

  it('does not let a closed dialog interfere with the open one', async () => {
    const user = userEvent.setup();
    render(
      <>
        <Harness />
        <Dialog open={false} title="Inactive" onClose={() => undefined}>
          <button type="button">inactive action</button>
        </Dialog>
      </>,
    );
    const dialog = await openDialog(user);

    await user.tab();

    expect(dialog).toContainElement(document.activeElement as HTMLElement);
    expect(screen.queryByRole('dialog', { name: 'Inactive' })).not.toBeInTheDocument();
  });

  it('cycles only through usable controls (skips disabled, hidden and aria-hidden)', async () => {
    const user = userEvent.setup();
    render(
      <div>
        <button type="button">trigger outside</button>
        <Dialog open title="Filtered" onClose={() => undefined}>
          <button type="button">first usable</button>
          <button type="button" disabled>
            disabled control
          </button>
          <button type="button" hidden>
            hidden control
          </button>
          <div aria-hidden="true">
            <button type="button">aria hidden control</button>
          </div>
          <button type="button" style={{ display: 'none' }}>
            display none control
          </button>
          <button type="button">last usable</button>
        </Dialog>
      </div>,
    );
    const dialog = screen.getByRole('dialog', { name: 'Filtered' });
    screen.getByRole('button', { name: 'last usable' }).focus();

    await user.tab();
    expect(screen.getByRole('button', { name: 'first usable' })).toHaveFocus();

    await user.tab({ shift: true });
    expect(screen.getByRole('button', { name: 'last usable' })).toHaveFocus();
    expect(dialog).toContainElement(document.activeElement as HTMLElement);
  });
});

describe('Dialog focus restoration (F-P21-ACC-01B)', () => {
  it('returns focus to the trigger when closed through its close control', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const trigger = screen.getByRole('button', { name: 'open dialog' });
    await openDialog(user);

    await user.click(screen.getByRole('button', { name: 'close dialog' }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(document.activeElement).not.toBe(document.body);
    expect(trigger).toHaveFocus();
  });

  it('returns focus to the trigger on Escape', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const trigger = screen.getByRole('button', { name: 'open dialog' });
    await openDialog(user);

    await user.keyboard('{Escape}');

    expect(document.activeElement).not.toBe(document.body);
    expect(trigger).toHaveFocus();
  });

  it('does not touch focus when the trigger is gone (no exception, no body hand-off)', async () => {
    const user = userEvent.setup();
    render(<Harness removeTriggerOnOpen />);
    await openDialog(user);

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'open dialog' })).not.toBeInTheDocument();
  });
});
