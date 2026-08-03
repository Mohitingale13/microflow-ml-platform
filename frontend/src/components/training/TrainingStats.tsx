import { Zap, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { RunListItem } from '@/types/experiment.types';

interface TrainingStatsProps {
  runs: RunListItem[];
}



export function TrainingStats({ runs }: TrainingStatsProps) {
  const activeCount = runs.filter((r) => r.status === 'running').length;
  const queuedCount = runs.filter((r) => r.status === 'queued').length;
  const completedCount = runs.filter((r) => r.status === 'completed').length;
  const failedCount = runs.filter((r) => r.status === 'failed').length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Active Runs */}
      <div className="bg-surface border border-border rounded-xl p-5 relative overflow-hidden transition-all hover:border-accent-blue/40">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Active Runs
          </span>
          <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center text-accent-blue">
            <Zap className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-text-primary tracking-tight">
            {activeCount}
          </span>
          {activeCount > 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-accent-blue font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-blue animate-pulse" />
              training now
            </span>
          )}
        </div>
      </div>

      {/* Queued Runs */}
      <div className="bg-surface border border-border rounded-xl p-5 relative overflow-hidden transition-all hover:border-amber-500/40">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Queued Runs
          </span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
            <Clock className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-text-primary tracking-tight">
            {queuedCount}
          </span>
          <span className="text-xs text-text-muted">ready to execute</span>
        </div>
      </div>

      {/* Completed Today */}
      <div className="bg-surface border border-border rounded-xl p-5 relative overflow-hidden transition-all hover:border-accent-emerald/40">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Completed Runs
          </span>
          <div className="w-8 h-8 rounded-lg bg-accent-emerald/10 flex items-center justify-center text-accent-emerald">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-text-primary tracking-tight">
            {completedCount}
          </span>
          <span className="text-xs text-text-muted">successful executions</span>
        </div>
      </div>

      {/* Failed Runs */}
      <div className="bg-surface border border-border rounded-xl p-5 relative overflow-hidden transition-all hover:border-accent-red/40">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Failed Runs
          </span>
          <div className="w-8 h-8 rounded-lg bg-accent-red/10 flex items-center justify-center text-accent-red">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-text-primary tracking-tight">
            {failedCount}
          </span>
          <span className="text-xs text-text-muted">requiring review</span>
        </div>
      </div>
    </div>
  );
}
