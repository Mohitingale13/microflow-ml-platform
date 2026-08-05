import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { useMemo } from 'react';
import type { DatasetPreview } from '../../types/dataset.types';

interface PreviewTableProps {
  preview: DatasetPreview;
}

export function PreviewTable({ preview }: PreviewTableProps) {
  // Since columns are dynamic based on the dataset, we generate them dynamically
  const columns = useMemo(() => {
    const helper = createColumnHelper<Record<string, any>>();
    
    return preview.columns.map(colName => 
      helper.accessor(row => row[colName], {
        id: colName,
        header: colName,
        cell: info => {
          const val = info.getValue();
          if (val === null || val === undefined) {
            return <span className="text-text-muted italic">null</span>;
          }
          return <span className="truncate max-w-[200px] inline-block">{String(val)}</span>;
        }
      })
    );
  }, [preview.columns]);

  const table = useReactTable({
    data: preview.rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="flex flex-col h-full border border-border rounded-lg overflow-hidden bg-surface">
      <div className="px-4 py-3 border-b border-border bg-surface-2 flex justify-between items-center">
        <h3 className="text-sm font-medium text-text-primary">Data Preview</h3>
        <span className="flex items-center gap-1.5 flex-wrap text-xs text-text-muted">
          <span>Showing</span>
          <strong className="text-text-primary font-semibold px-0.5">{preview.rows.length}</strong>
          <span>of</span>
          <strong className="text-text-primary font-semibold px-0.5">{preview.total_rows?.toLocaleString() ?? '?'}</strong>
          <span>rows</span>
        </span>
      </div>
      
      <div className="overflow-auto flex-1">
        <table className="w-full text-left border-collapse min-w-max">
          <thead className="sticky top-0 bg-surface-2 backdrop-blur z-10 shadow-[0_1px_0_var(--color-border)]">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-4 py-2 text-xs font-medium tracking-wider text-text-muted border-r border-border last:border-r-0 whitespace-nowrap"
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-white/5 transition-colors">
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-4 py-2 text-sm text-text-primary border-r border-border last:border-r-0 whitespace-nowrap">
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext()
                    )}
                  </td>
                ))}
              </tr>
            ))}
            {preview.rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-text-muted">
                  No preview data available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
