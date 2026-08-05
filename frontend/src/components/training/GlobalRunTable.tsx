import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Play,
  PlayCircle,
  XCircle,
  ChevronRight,
  Loader2,
  Database,
  FlaskConical,
} from 'lucide-react';
import { RunStatusBadge } from '@/components/experiments/RunStatusBadge';
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog';
import { formatModelType } from '@/utils/format';
import type { RunListItem, ExperimentListItem } from '@/types/experiment.types';
import type { DatasetListItem } from '@/types/dataset.types';

interface GlobalRunTableProps {
  runs: RunListItem[];
  experimentsMap: Map<string, ExperimentListItem>;
  datasetsMap: Map<string, DatasetListItem>;
  onExecuteClick: (run: RunListItem) => void;
  onQueueRun?: (runId: string, experimentId: string) => Promise<void>;
  onCancelRun?: (runId: string, experimentId: string) => Promise<void>;
  isActionLoading?: boolean;
}

function formatDate(iso: string) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(run: RunListItem): string {
  if (!run.created_at || !run.updated_at) return '—';
  if (run.status === 'draft' || run.status === 'queued') return '—';

  const start = new Date(run.created_at).getTime();
  const end =
    run.status === 'running'
      ? Date.now()
      : new Date(run.updated_at).getTime();

  const diffMs = Math.max(0, end - start);
  if (diffMs < 500) return '< 1s';
  if (diffMs < 60000) return `${(diffMs / 1000).toFixed(1)}s`;
  const mins = Math.floor(diffMs / 60000);
  const secs = Math.floor((diffMs % 60000) / 1000);
  return `${mins}m ${secs}s`;
}

export function GlobalRunTable({
  runs,
  experimentsMap,
  datasetsMap,
  onExecuteClick,
  onQueueRun,
  onCancelRun,
  isActionLoading = false,
}: GlobalRunTableProps) {
  const navigate = useNavigate();
  const [confirmCancelRun, setConfirmCancelRun] = useState<RunListItem | null>(null);

  const handleConfirmCancel = async () => {
    if (!confirmCancelRun || !onCancelRun) return;
    try {
      await onCancelRun(confirmCancelRun.id, confirmCancelRun.experiment_id);
    } finally {
      setConfirmCancelRun(null);
    }
  };

  return (
    <>
      <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[900px]">
            <thead>
              <tr className="bg-surface-2 border-b border-border text-xs font-semibold uppercase tracking-wider text-text-muted">
                <th className="px-4 py-3.5">Run</th>
                <th className="px-4 py-3.5">Experiment</th>
                <th className="px-4 py-3.5">Dataset</th>
                <th className="px-4 py-3.5">Model</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5 text-center">Actions</th>
                <th className="px-4 py-3.5">Created</th>
                <th className="px-4 py-3.5">Updated</th>
                <th className="px-4 py-3.5">Duration</th>
                <th className="px-4 py-3.5 text-center">Primary Metric</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-sm">
              {runs.map((run) => {
                const experiment = experimentsMap.get(run.experiment_id);
                const dataset = experiment ? datasetsMap.get(experiment.dataset_id) : undefined;
                const isQueued = run.status === 'queued';
                const isDraft = run.status === 'draft';
                const isRunning = run.status === 'running';

                return (
                  <tr
                    key={run.id}
                    className="hover:bg-surface-2/60 transition-colors group"
                  >
                    {/* Run Number */}
                    <td className="px-4 py-3.5 font-mono font-bold text-text-primary">
                      <Link
                        to={`/runs/${run.id}`}
                        className="hover:text-accent-blue transition-colors inline-flex items-center gap-1"
                      >
                        #{run.run_number}
                      </Link>
                    </td>

                    {/* Experiment Name */}
                    <td className="px-4 py-3.5">
                      {experiment ? (
                        <Link
                          to={`/experiments/${experiment.id}`}
                          className="font-medium text-text-primary hover:text-accent-blue transition-colors flex items-center gap-1.5 truncate max-w-[180px]"
                          title={experiment.name}
                        >
                          <FlaskConical className="w-3.5 h-3.5 text-text-muted shrink-0" />
                          <span className="truncate">{experiment.name}</span>
                        </Link>
                      ) : (
                        <span className="text-xs font-mono text-text-muted">
                          {run.experiment_id.slice(0, 8)}…
                        </span>
                      )}
                    </td>

                    {/* Dataset Name */}
                    <td className="px-4 py-3.5">
                      {dataset ? (
                        <Link
                          to={`/datasets/${dataset.id}`}
                          className="text-xs font-medium text-text-secondary hover:text-accent-blue transition-colors inline-flex items-center gap-1 bg-surface-2 px-2 py-0.5 rounded border border-border truncate max-w-[150px]"
                          title={dataset.name}
                        >
                          <Database className="w-3 h-3 text-text-muted shrink-0" />
                          <span className="truncate">{dataset.name}</span>
                        </Link>
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                    </td>

                    {/* Model Type */}
                    <td className="px-4 py-3.5">
                      {run.model_type ? (
                        <span className="text-xs font-mono text-text-secondary bg-surface-2 px-2 py-0.5 rounded border border-border whitespace-nowrap">
                          {formatModelType(run.model_type)}
                        </span>
                      ) : (
                        <span className="text-xs text-text-muted">Inherit (RF)</span>
                      )}
                    </td>

                    {/* Status Badge */}
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <RunStatusBadge status={run.status} size="sm" />
                    </td>
                    {/* Actions */}
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="flex items-center justify-center gap-1.5">
                        {/* Execute Action */}
                        {isQueued && (
                          <button
                            onClick={() => onExecuteClick(run)}
                            disabled={isActionLoading}
                            title="Execute training now"
                            className="px-2.5 py-1 text-xs font-medium text-white bg-accent-blue hover:opacity-90 rounded inline-flex items-center gap-1 transition-colors shadow-sm disabled:opacity-50"
                          >
                            <Play className="w-3 h-3 fill-current" />
                            Execute
                          </button>
                        )}

                        {/* Quick Queue */}
                        {isDraft && onQueueRun && (
                          <button
                            onClick={() => onQueueRun(run.id, run.experiment_id)}
                            disabled={isActionLoading}
                            title="Queue run"
                            className="p-1.5 rounded text-amber-400 hover:bg-amber-500/10 transition-colors disabled:opacity-50"
                          >
                            <PlayCircle className="w-4 h-4" />
                          </button>
                        )}

                        {/* Running indicator */}
                        {isRunning && (
                          <span
                            title="Training in progress"
                            className="p-1.5 text-accent-blue inline-flex items-center"
                          >
                            <Loader2 className="w-4 h-4 animate-spin" />
                          </span>
                        )}

                        {/* Cancel Action */}
                        {(isQueued || isDraft) && onCancelRun && (
                          <button
                            onClick={() => setConfirmCancelRun(run)}
                            disabled={isActionLoading || isRunning}
                            title="Cancel run"
                            className="p-1.5 rounded text-text-muted hover:text-accent-red hover:bg-accent-red/10 transition-colors disabled:opacity-50"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}

                        {/* View Details */}
                        <button
                          onClick={() => navigate(`/runs/${run.id}`)}
                          title="View Run Details"
                          className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </td>

                    {/* Created */}
                    <td className="px-4 py-3.5 text-xs text-text-muted whitespace-nowrap">
                      {formatDate(run.created_at)}
                    </td>

                    {/* Updated */}
                    <td className="px-4 py-3.5 text-xs text-text-muted whitespace-nowrap">
                      {formatDate(run.updated_at)}
                    </td>

                    {/* Duration */}
                    <td className="px-4 py-3.5 text-xs font-mono text-text-secondary whitespace-nowrap">
                      {formatDuration(run)}
                    </td>

                    {/* Primary Metric */}
                    <td className="px-4 py-3.5 text-center text-xs font-mono text-text-muted">
                      {/* Placeholder for future stored metrics */}
                      —
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cancel Confirmation */}
      {confirmCancelRun && (
        <ConfirmationDialog
          isOpen
          title={`Cancel Run #${confirmCancelRun.run_number}`}
          description="Are you sure you want to cancel this run? This action cannot be undone."
          confirmLabel="Cancel Run"
          onConfirm={handleConfirmCancel}
          onCancel={() => setConfirmCancelRun(null)}
          isLoading={isActionLoading}
          variant="danger"
        />
      )}
    </>
  );
}
