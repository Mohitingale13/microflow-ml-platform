/**
 * RecentRunsTable.tsx — Table of the 10 most recent training runs.
 */

import { useNavigate } from 'react-router-dom';
import { ExternalLink, List, ChevronRight } from 'lucide-react';
import type { RecentRunItem } from '@/types/dashboard.types';
import { formatRelativeTime } from '@/utils/time';

interface RecentRunsTableProps {
  runs: RecentRunItem[];
  isLoading: boolean;
}

const STATUS_STYLES: Record<string, { label: string; class: string }> = {
  completed: { label: 'Completed', class: 'badge-success' },
  running:   { label: 'Running',   class: 'badge-running' },
  failed:    { label: 'Failed',    class: 'badge-error' },
  queued:    { label: 'Queued',    class: 'badge-queued' },
  draft:     { label: 'Draft',     class: 'badge-default' },
  cancelled: { label: 'Cancelled', class: 'badge-default' },
};

function ModelTag({ model }: { model: string | null }) {
  if (!model) return <span className="text-muted-foreground text-xs">—</span>;
  const label = model.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const colors: Record<string, string> = {
    random_forest:      'text-emerald-400',
    logistic_regression:'text-blue-400',
    xgboost:            'text-purple-400',
  };
  return (
    <span className={`text-xs font-medium ${colors[model] ?? 'text-text-secondary'}`}>
      {label}
    </span>
  );
}

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i} className="animate-pulse">
          {Array.from({ length: 8 }).map((_, j) => (
            <td key={j} className="px-3 py-3">
              <div className="h-3.5 bg-surface-2 rounded w-full" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export function RecentRunsTable({ runs, isLoading }: RecentRunsTableProps) {
  const navigate = useNavigate();

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title mb-0 flex items-center gap-2">
          <List size={16} className="text-accent-cyan" />
          Recent Runs
        </h3>
        <button
          onClick={() => navigate('/experiments')}
          className="btn btn-outline text-xs flex items-center gap-1"
        >
          View All
          <ChevronRight size={13} />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="table w-full">
          <thead>
            <tr>
              <th className="text-left px-3 py-2 text-xs text-muted-foreground font-medium">Run</th>
              <th className="text-left px-3 py-2 text-xs text-muted-foreground font-medium">Experiment</th>
              <th className="text-left px-3 py-2 text-xs text-muted-foreground font-medium hidden md:table-cell">Dataset</th>
              <th className="text-left px-3 py-2 text-xs text-muted-foreground font-medium">Model</th>
              <th className="text-left px-3 py-2 text-xs text-muted-foreground font-medium">Status</th>
              <th className="text-right px-3 py-2 text-xs text-muted-foreground font-medium">Accuracy</th>
              <th className="text-right px-3 py-2 text-xs text-muted-foreground font-medium hidden lg:table-cell">Completed</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {isLoading && <SkeletonRows />}

            {!isLoading && runs.length === 0 && (
              <tr>
                <td colSpan={8} className="py-10 text-center text-sm text-muted-foreground">
                  No runs yet. Execute a training run from an experiment to see results here.
                </td>
              </tr>
            )}

            {!isLoading && runs.map(run => {
              const statusStyle = STATUS_STYLES[run.status] ?? STATUS_STYLES.draft;
              return (
                <tr
                  key={run.run_id}
                  className="table-row cursor-pointer hover:bg-surface-2/50 transition-colors"
                  onClick={() => navigate(`/runs/${run.run_id}`)}
                >
                  <td className="px-3 py-2.5">
                    <span className="text-sm font-medium text-text-primary">#{run.run_number}</span>
                  </td>
                  <td className="px-3 py-2.5">
                    <button
                      className="text-sm text-blue-400 hover:underline text-left max-w-[140px] truncate block"
                      onClick={e => { e.stopPropagation(); navigate(`/experiments/${run.experiment_id}`); }}
                    >
                      {run.experiment_name}
                    </button>
                  </td>
                  <td className="px-3 py-2.5 hidden md:table-cell">
                    <span className="text-xs text-text-secondary truncate max-w-[100px] block">
                      {run.dataset_name ?? '—'}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <ModelTag model={run.model} />
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`badge badge-sm ${statusStyle.class}`}>
                      {statusStyle.label}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <span className="text-sm font-medium text-text-primary">
                      {run.accuracy != null ? `${(run.accuracy * 100).toFixed(1)}%` : '—'}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right hidden lg:table-cell">
                    <span className="text-xs text-muted-foreground">
                      {run.completed_at
                        ? formatRelativeTime(run.completed_at)
                        : '—'}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <ExternalLink size={13} className="text-muted-foreground" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
