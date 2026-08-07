import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowDown, ArrowUp, ArrowUpDown, Search } from 'lucide-react';
import { formatBytes } from '@/utils/format';
import { StatusBadge } from './StatusBadge';
import type { DatasetListItem } from '../../types/dataset.types';

const columnHelper = createColumnHelper<DatasetListItem>();

interface DatasetTableProps {
  data: DatasetListItem[];
  isLoading: boolean;
}

export function DatasetTable({ data, isLoading }: DatasetTableProps) {
  const navigate = useNavigate();
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo(
    () => [
      columnHelper.accessor('name', {
        header: 'Name',
        cell: (info) => (
          <div className="flex flex-col">
            <span className="font-medium text-text-primary">
              {info.getValue()}
            </span>
            <span className="text-xs text-text-muted mt-0.5 truncate max-w-[200px]">
              {info.row.original.description || 'No description'}
            </span>
          </div>
        ),
      }),
      columnHelper.accessor('version', {
        header: 'Version',
        cell: (info) => (
          <span className="text-xs font-mono text-text-muted bg-surface-2 px-1.5 py-0.5 rounded">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => <StatusBadge status={info.getValue()} />,
      }),
      columnHelper.accessor((row) => row.row_count, {
        id: 'rows',
        header: 'Rows',
        cell: (info) => (
          <span className="text-text-muted">
            {info.getValue()?.toLocaleString() ?? '-'}
          </span>
        ),
      }),
      columnHelper.accessor((row) => row.column_count, {
        id: 'columns',
        header: 'Columns',
        cell: (info) => (
          <span className="text-text-muted">
            {info.getValue()?.toLocaleString() ?? '-'}
          </span>
        ),
      }),
      columnHelper.accessor('file_size_bytes', {
        header: 'Size',
        cell: (info) => (
          <span className="text-text-muted text-sm">
            {formatBytes(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor('created_at', {
        header: 'Uploaded',
        cell: (info) => (
          <span className="text-text-muted text-sm">
            {new Date(info.getValue()).toLocaleDateString()}
          </span>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search datasets..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-surface border border-border rounded-md text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
          />
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border bg-surface-2">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase cursor-pointer hover:text-text-primary transition-colors group select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      <span className="text-border group-hover:text-text-muted">
                        {{
                          asc: <ArrowUp className="w-3.5 h-3.5" />,
                          desc: <ArrowDown className="w-3.5 h-3.5" />,
                        }[header.column.getIsSorted() as string] ?? (
                          <ArrowUpDown className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100" />
                        )}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-text-muted">
                  Loading datasets...
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center">
                  <p className="text-text-muted">No datasets found.</p>
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => navigate(`/datasets/${row.original.id}`)}
                  className="hover:bg-[var(--color-surface-2)] cursor-pointer transition-colors group"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 align-middle">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
