/** Form primitive tests (Appendix AL §35, §39). */

import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { Field, TextField } from './Field';
import { Input } from '../Input';
import { Select } from '../Select';

function TextFieldHarness() {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | undefined>(undefined);
  return (
    <>
      <TextField label="Login" value={value} onChange={setValue} error={error} />
      <button type="button" onClick={() => setError('Login is required')}>
        trigger error
      </button>
    </>
  );
}

describe('Field / TextField', () => {
  it('associates the label with the control', () => {
    render(<TextField label="Login" value="" onChange={() => undefined} />);

    const input = screen.getByLabelText('Login');
    expect(input).toBeInstanceOf(HTMLInputElement);
    expect(input).not.toHaveAttribute('aria-invalid');
  });

  it('links the error message and marks the control invalid', async () => {
    const user = userEvent.setup();
    render(<TextFieldHarness />);

    await user.click(screen.getByRole('button', { name: 'trigger error' }));

    const input = screen.getByLabelText('Login');
    const error = screen.getByRole('alert');
    expect(error).toHaveTextContent('Login is required');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input.getAttribute('aria-describedby')).toContain(error.id);
  });

  it('forwards typed values through onChange', async () => {
    const user = userEvent.setup();
    render(<TextFieldHarness />);

    await user.type(screen.getByLabelText('Login'), 'ada');

    expect(screen.getByLabelText('Login')).toHaveValue('ada');
  });

  it('describes the control with hint and error together', () => {
    render(
      <Field label="Password" hint="At least 12 characters" error="Too short">
        {({ id, describedBy, invalid }) => (
          <Input id={id} aria-describedby={describedBy} invalid={invalid} />
        )}
      </Field>,
    );

    const input = screen.getByLabelText('Password');
    expect(input).toHaveAccessibleDescription('At least 12 characters Too short');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders a labelled native select', () => {
    render(
      <Field label="Status">
        {({ id }) => (
          <Select id={id} defaultValue="active">
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
          </Select>
        )}
      </Field>,
    );

    expect(screen.getByLabelText('Status')).toHaveValue('active');
  });
});
