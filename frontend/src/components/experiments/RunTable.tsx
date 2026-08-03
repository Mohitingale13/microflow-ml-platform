import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, XCircle, ChevronRight, Terminal } from 'lucide-react';
import { RunStatusBadge } from './RunStatusBadge';
import { ConfirmationDialog } from '../common/ConfirmationDialog';
import { useQueueRun, useCancelRun } from '@/hooks/useExperiments';
import { formatModelType } from '@/utils/format';
import type { RunListItem } from '@/types/experiment.types';

interface RunTableProps {
  runs: RunListItem[];
  experimentId: string;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

const QUEUEABLE: RunListItem['status'][] = ['draft'];
const CANCELLABLE: RunListItem['status'][] = ['draft', 'queued'];

export function RunTable({ runs, experimentId }: RunTableProps) {
  const navigate = useNavigate();
  const [confirmAction, setConfirmAction] = useState<{
    type: 'queue' | 'cancel';
    runId: string;
    runNumber: number;
  } | null>(null);

  const queueMutation = useQueueRun();
  const cancelMutation = useCancelRun();

  const handleConfirm = async () => {
    if (!confirmAction) return;
    try {
      if (confirmAction.type === 'queue') {
        await queueMutation.mutateAsync({ id: confirmAction.runId, experimentId });
      } else {
        await cancelMutation.mutateAsync({ id: confirmAction.runId, experimentId });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setConfirmAction(null);
    }
  };

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-12 h-12 rounded-full bg-surface-2 flex items-center justify-center mb-3">
          <Terminal className="w-5 h-5 text-text-muted" />
        </div>
        <p className="text-sm font-medium text-text-primary mb-1">No runs yet</p>
        <p className="text-xs text-text-muted">Create a run to start an execution.</p>
      </div>
    );
  }

  const isActing = queueMutation.isPending || cancelMutation.isPending;

  return (
    <>
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-2 border-b border-border">
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Run</th>
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Status</th>
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden md:table-cell">Model</th>
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden lg:table-cell">Created</th>
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden lg:table-cell">Updated</th>
              <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {runs.map((run) => (
              <tr key={run.id} className="hover:bg-surface-2 transition-colors group">
                <td className="px-4 py-4">
                  <span className="text-sm font-mono font-semibold text-text-primary">
                    #{run.run_number}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <RunStatusBadge status={run.status} />
                </td>
                <td className="px-4 py-4 hidden md:table-cell">
                  {run.model_type ? (
                    <span className="text-xs font-mono text-text-secondary bg-surface-2 px-2 py-1 rounded border border-border">
                      {formatModelType(run.model_type)}
                    </span>
                  ) : (
                    <span className="text-xs text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-4 hidden lg:table-cell">
                  <span className="text-xs text-text-muted">{formatDate(run.created_at)}</span>
                </td>
                <td className="px-4 py-4 hidden lg:table-cell">
                  <span className="text-xs text-text-muted">{formatDate(run.updated_at)}</span>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center justify-end gap-1.5">
                    {QUEUEABLE.includes(run.status) && (
                      <button
                        onClick={() => setConfirmAction({ type: 'queue', runId: run.id, runNumber: run.run_number })}
                        disabled={isActing}
                        title="Queue run"
                        className="p-1.5 rounded text-text-muted hover:text-accent-blue hover:bg-accent-blue/10 transition-colors disabled:opacity-50"
                      >
                        <PlayCircle className="w-4 h-4" />
                      </button>
                    )}
                    {CANCELLABLE.includes(run.status) && (
                      <button
                        onClick={() => setConfirmAction({ type: 'cancel', runId: run.id, runNumber: run.run_number })}
                        disabled={isActing}
                        title="Cancel run"
                        className="p-1.5 rounded text-text-muted hover:text-accent-red hover:bg-accent-red/10 transition-colors disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/runs/${run.id}`)}
                      title="View details"
                      className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {confirmAction && (
        <ConfirmationDialog
          isOpen
          title={
            confirmAction.type === 'queue'
              ? `Queue Run #${confirmAction.runNumber}`
              : `Cancel Run #${confirmAction.runNumber}`
          }
          description={
            confirmAction.type === 'queue'
              ? 'This will move the run to the queued state, ready for execution.'
              : 'This will cancel the run. This action cannot be undone.'
          }
          confirmLabel={confirmAction.type === 'queue' ? 'Queue' : 'Cancel Run'}
          onConfirm={handleConfirm}
          onCancel={() => setConfirmAction(null)}
          isLoading={isActing}
          variant={confirmAction.type === 'cancel' ? 'danger' : 'warning'}
        />
      )}
    </>
  );
}
