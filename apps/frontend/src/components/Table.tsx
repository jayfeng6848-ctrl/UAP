import type { ReactNode } from 'react';

import styles from './Table.module.css';

export interface TableColumn<Row> {
  key: string;
  header: string;
  render: (row: Row) => ReactNode;
}

export interface TableProps<Row> {
  columns: Array<TableColumn<Row>>;
  rows: Row[];
  rowKey: (row: Row) => string;
  loading?: boolean;
  emptyMessage?: string;
}

/**
 * Presentation-only table: columns, rows, empty and loading states. It offers no
 * pagination, sorting or query DSL — the Company API freezes none of those.
 */
export function Table<Row>({
  columns,
  rows,
  rowKey,
  loading = false,
  emptyMessage = 'No records.',
}: TableProps<Row>) {
  if (loading) {
    return (
      <p role="status" aria-live="polite">
        Loading…
      </p>
    );
  }
  if (rows.length === 0) {
    return <p data-testid="uap-table-empty">{emptyMessage}</p>;
  }
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col">
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={rowKey(row)}>
            {columns.map((column) => (
              <td key={column.key}>{column.render(row)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
