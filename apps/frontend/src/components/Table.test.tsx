/**
 * Table primitive tests (Appendix AL §37).
 *
 * Presentation only: columns, rows, empty and loading. No pagination, sorting or
 * query DSL — the Company API freezes none of those.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Table } from './Table';

interface Row {
  id: string;
  name: string;
}

const columns = [
  { key: 'name', header: 'Name', render: (row: Row) => row.name },
];

describe('Table', () => {
  it('renders column headers and rows', () => {
    render(
      <Table
        columns={columns}
        rows={[{ id: '1', name: 'Ada' }]}
        rowKey={(row) => row.id}
      />,
    );

    expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'Ada' })).toBeInTheDocument();
  });

  it('renders an empty message when there are no rows', () => {
    render(
      <Table columns={columns} rows={[]} rowKey={(row) => row.id} emptyMessage="Nothing here" />,
    );

    expect(screen.getByTestId('uap-table-empty')).toHaveTextContent('Nothing here');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('announces loading instead of rendering stale rows', () => {
    render(<Table columns={columns} rows={[{ id: '1', name: 'Ada' }]} rowKey={(row) => row.id} loading />);

    expect(screen.getByRole('status')).toHaveTextContent('Loading…');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
