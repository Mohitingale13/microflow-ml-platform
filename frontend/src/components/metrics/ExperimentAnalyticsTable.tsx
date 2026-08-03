/**
 * ExperimentAnalyticsTable.tsx — Experiment-level metrics & performance summary.
 */

import { Link } from 'react-router-dom';
import { ExternalLink, FlaskConical, Trophy } from 'lucide-react';
import type { ExperimentMetricSummary } from '@/types/metrics.types';
import { formatDate } from '@/utils/format';

interface ExperimentAnalyticsTableProps {
  experiments: ExperimentMetricSummary[];
  isLoading: boolean;
}

export function ExperimentAnalyticsTable({
  experiments,
  isLoading,
}: ExperimentAnalyticsTableProps) {
  if (isLoading) {
    return (
      <div className="card p-6 animate-pulse">
        <div className="h-6 bg-muted/60 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 bg-muted/40 rounded w-full"></div>
          ))}
        </div>
      </div>
    );
  }

  if (experiments.length === 0) {
    return (
      <div className="card p-8 text-center text-muted-foreground border-dashed">
        <FlaskConical className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm font-medium">No experiments found</p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Create experiments and execute runs to see analytics here.
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <FlaskConical size={16} className="text-primary" />
            Experiment Analytics
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Aggregated metrics, best runs, and progress across all experiments
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground bg-muted/50 px-2.5 py-1 rounded">
          {experiments.length} {experiments.length === 1 ? 'experiment' : 'experiments'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/40 border-b border-border text-muted-foreground">
            <tr>
              <th className="py-3 px-4">Experiment</th>
              <th className="py-3 px-4">Dataset</th>
              <th className="py-3 px-4 text-center">Total Runs</th>
              <th className="py-3 px-4">Best Run</th>
              <th className="py-3 px-4 text-right">Best Accuracy</th>
              <th className="py-3 px-4 text-right">Avg Accuracy</th>
              <th className="py-3 px-4">Latest Run</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {experiments.map((exp) => (
              <tr key={exp.experiment_id} className="hover:bg-muted/30 transition-colors">
                {/* Experiment Link */}
                <td className="py-3.5 px-4 font-medium text-foreground">
                  <Link
                    to={`/experiments/${exp.experiment_id}`}
                    className="hover:text-primary transition-colors flex items-center gap-1.5 font-medium"
                  >
                    <span>{exp.experiment_name}</span>
                    <ExternalLink size={11} className="text-muted-foreground opacity-50" />
                  </Link>
                </td>

                {/* Dataset Link */}
                <td className="py-3.5 px-4 text-muted-foreground">
                  {exp.dataset_id ? (
                    <Link
                      to={`/datasets/${exp.dataset_id}`}
                      className="hover:text-primary transition-colors inline-flex items-center gap-1"
                    >
                      <span>{exp.dataset_name}</span>
                    </Link>
                  ) : (
                    <span>—</span>
                  )}
                </td>

                {/* Runs */}
                <td className="py-3.5 px-4 text-center font-mono text-foreground font-medium">
                  {exp.total_runs}
                </td>

                {/* Best Run */}
                <td className="py-3.5 px-4 font-mono">
                  {exp.best_run_id ? (
                    <Link
                      to={`/runs/${exp.best_run_id}`}
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      <Trophy size={12} className="text-amber-400" />
                      <span>Run #{exp.best_run_number}</span>
                    </Link>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>

                {/* Best Accuracy */}
                <td className="py-3.5 px-4 text-right font-mono font-semibold text-emerald-400">
                  {exp.best_accuracy !== null ? `${(exp.best_accuracy * 100).toFixed(2)}%` : '—'}
                </td>

                {/* Avg Accuracy */}
                <td className="py-3.5 px-4 text-right font-mono text-foreground">
                  {exp.average_accuracy !== null ? `${(exp.average_accuracy * 100).toFixed(2)}%` : '—'}
                </td>

                {/* Latest Run Info */}
                <td className="py-3.5 px-4 text-muted-foreground">
                  {exp.latest_run_id ? (
                    <div className="flex flex-col">
                      <Link
                        to={`/runs/${exp.latest_run_id}`}
                        className="hover:text-primary font-mono text-[11px]"
                      >
                        Run #{exp.latest_run_number} ({exp.latest_run_status})
                      </Link>
                      {exp.latest_run_created_at && (
                        <span className="text-[10px] text-muted-foreground/70">
                          {formatDate(exp.latest_run_created_at)}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
