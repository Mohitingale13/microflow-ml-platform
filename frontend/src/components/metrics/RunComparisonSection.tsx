/**
 * RunComparisonSection.tsx — Interactive multi-run comparison table and selector.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckSquare,
  Layers,
  Sparkles,
  Square,
  Trash2,
  TrendingUp,
} from 'lucide-react';
import { useRunComparison } from '@/hooks/useMetrics';
import type { Run, RunListItem } from '@/types/experiment.types';

interface RunComparisonSectionProps {
  availableRuns: (Run | RunListItem)[];
  experimentNames: Record<string, string>;
}

export function RunComparisonSection({
  availableRuns,
  experimentNames,
}: RunComparisonSectionProps) {
  // Only completed runs can be compared
  const completedRuns = availableRuns.filter((r) => r.status === 'completed');

  const [selectedRunIds, setSelectedRunIds] = useState<string[]>(() => {
    // Default to first 2-3 completed runs if available
    return completedRuns.slice(0, 3).map((r) => r.id);
  });

  const { data: comparisonItems = [], isLoading } = useRunComparison(selectedRunIds);

  const toggleRun = (runId: string) => {
    setSelectedRunIds((prev) =>
      prev.includes(runId) ? prev.filter((id) => id !== runId) : [...prev, runId]
    );
  };

  const handleSelectAllCompleted = () => {
    setSelectedRunIds(completedRuns.slice(0, 6).map((r) => r.id));
  };

  const handleClearAll = () => {
    setSelectedRunIds([]);
  };

  // Compute best values for metric highlighting
  const bestValues = {
    accuracy: Math.max(...comparisonItems.map((c) => c.accuracy ?? -1)),
    precision: Math.max(...comparisonItems.map((c) => c.precision ?? -1)),
    recall: Math.max(...comparisonItems.map((c) => c.recall ?? -1)),
    f1: Math.max(...comparisonItems.map((c) => c.f1 ?? -1)),
    roc_auc: Math.max(...comparisonItems.map((c) => c.roc_auc ?? -1)),
    duration: Math.min(
      ...comparisonItems.filter((c) => c.duration !== null).map((c) => c.duration!)
    ),
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <TrendingUp size={16} className="text-emerald-400" />
            Side-by-Side Run Comparison
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Select 2 or more completed runs to compare evaluation metrics and hyperparameters
          </p>
        </div>

        {/* Quick Action Controls */}
        <div className="flex items-center gap-2">
          {completedRuns.length > 0 && (
            <button
              onClick={handleSelectAllCompleted}
              className="btn btn-outline text-xs py-1.5 px-3"
            >
              <Sparkles size={13} className="text-amber-400" />
              <span>Select Top Runs</span>
            </button>
          )}
          {selectedRunIds.length > 0 && (
            <button
              onClick={handleClearAll}
              className="btn btn-ghost text-xs py-1.5 px-3 text-muted-foreground hover:text-destructive"
            >
              <Trash2 size={13} />
              <span>Clear Selection</span>
            </button>
          )}
        </div>
      </div>

      {/* Interactive Run Selector Chips */}
      <div className="p-4 bg-muted/20 border-b border-border">
        <div className="text-xs font-medium text-muted-foreground mb-2 flex items-center justify-between">
          <span>Select runs to include ({selectedRunIds.length} selected):</span>
          <span className="text-[11px] font-mono">{completedRuns.length} completed runs available</span>
        </div>

        {completedRuns.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">
            No completed runs available. Execute runs to compare them.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto pr-1">
            {completedRuns.map((run) => {
              const isSelected = selectedRunIds.includes(run.id);
              const expName = experimentNames[run.experiment_id] || 'Experiment';
              const modelName = run.model_type ? run.model_type.replace(/_/g, ' ') : 'default';

              return (
                <button
                  key={run.id}
                  onClick={() => toggleRun(run.id)}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-mono transition-all border ${
                    isSelected
                      ? 'bg-primary/15 border-primary text-primary-foreground font-semibold shadow-sm'
                      : 'bg-card/70 border-border text-muted-foreground hover:border-muted-foreground/50 hover:bg-muted/40'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare size={13} className="text-primary" />
                  ) : (
                    <Square size={13} className="text-muted-foreground/60" />
                  )}
                  <span>
                    Run #{run.run_number} ({expName} · {modelName})
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Comparison Table */}
      {selectedRunIds.length === 0 ? (
        <div className="p-8 text-center text-muted-foreground border-dashed">
          <Layers className="mx-auto h-8 w-8 text-muted-foreground/40 mb-2" />
          <p className="text-sm font-medium">Select runs above to see comparison matrix</p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            Choose at least 2 completed runs for side-by-side metric differences.
          </p>
        </div>
      ) : isLoading ? (
        <div className="p-6 animate-pulse space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 bg-muted/40 rounded w-full"></div>
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/40 border-b border-border text-muted-foreground">
              <tr>
                <th className="py-3 px-4">Run</th>
                <th className="py-3 px-4">Experiment</th>
                <th className="py-3 px-4">Dataset</th>
                <th className="py-3 px-4">Model</th>
                <th className="py-3 px-4 text-right">Accuracy</th>
                <th className="py-3 px-4 text-right">Precision</th>
                <th className="py-3 px-4 text-right">Recall</th>
                <th className="py-3 px-4 text-right">F1 Score</th>
                <th className="py-3 px-4 text-right">ROC AUC</th>
                <th className="py-3 px-4 text-right">Duration</th>
                <th className="py-3 px-4">Hyperparameters / Config</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {comparisonItems.map((item) => {
                const isTopAcc =
                  item.accuracy !== null &&
                  item.accuracy === bestValues.accuracy &&
                  comparisonItems.length > 1;
                const isTopF1 =
                  item.f1 !== null && item.f1 === bestValues.f1 && comparisonItems.length > 1;

                return (
                  <tr key={item.run_id} className="hover:bg-muted/30 transition-colors">
                    {/* Run */}
                    <td className="py-3.5 px-4 font-mono font-medium">
                      <Link
                        to={`/runs/${item.run_id}`}
                        className="text-primary hover:underline inline-flex items-center gap-1"
                      >
                        <span>Run #{item.run_number}</span>
                      </Link>
                    </td>

                    {/* Experiment */}
                    <td className="py-3.5 px-4 text-muted-foreground">
                      <Link
                        to={`/experiments/${item.experiment_id}`}
                        className="hover:text-foreground transition-colors"
                      >
                        {item.experiment_name}
                      </Link>
                    </td>

                    {/* Dataset */}
                    <td className="py-3.5 px-4 text-muted-foreground">
                      {item.dataset_id ? (
                        <Link
                          to={`/datasets/${item.dataset_id}`}
                          className="hover:text-foreground transition-colors"
                        >
                          {item.dataset_name}
                        </Link>
                      ) : (
                        <span>—</span>
                      )}
                    </td>

                    {/* Model */}
                    <td className="py-3.5 px-4 font-mono text-foreground font-medium">
                      <span className="bg-muted/60 px-2 py-0.5 rounded text-[11px]">
                        {item.model ? item.model.replace(/_/g, ' ').toUpperCase() : 'DEFAULT'}
                      </span>
                    </td>

                    {/* Accuracy */}
                    <td className="py-3.5 px-4 text-right font-mono font-semibold">
                      {item.accuracy !== null ? (
                        <span
                          className={
                            isTopAcc
                              ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded'
                              : 'text-foreground'
                          }
                        >
                          {(item.accuracy * 100).toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>

                    {/* Precision */}
                    <td className="py-3.5 px-4 text-right font-mono text-foreground">
                      {item.precision !== null ? `${(item.precision * 100).toFixed(2)}%` : '—'}
                    </td>

                    {/* Recall */}
                    <td className="py-3.5 px-4 text-right font-mono text-foreground">
                      {item.recall !== null ? `${(item.recall * 100).toFixed(2)}%` : '—'}
                    </td>

                    {/* F1 */}
                    <td className="py-3.5 px-4 text-right font-mono font-medium">
                      {item.f1 !== null ? (
                        <span className={isTopF1 ? 'text-purple-400 font-bold' : 'text-foreground'}>
                          {(item.f1 * 100).toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>

                    {/* ROC AUC */}
                    <td className="py-3.5 px-4 text-right font-mono text-cyan-400">
                      {item.roc_auc !== null ? item.roc_auc.toFixed(4) : '—'}
                    </td>

                    {/* Duration */}
                    <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">
                      {item.duration !== null ? `${item.duration.toFixed(2)}s` : '—'}
                    </td>

                    {/* Hyperparameters Config */}
                    <td className="py-3.5 px-4">
                      {item.training_configuration &&
                      Object.keys(item.training_configuration).length > 0 ? (
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {Object.entries(item.training_configuration).map(([k, v]) => (
                            <span
                              key={k}
                              className="inline-flex items-center text-[10px] font-mono bg-muted/60 text-muted-foreground px-1.5 py-0.5 rounded"
                            >
                              <span className="text-foreground/70 mr-1">{k}:</span>
                              <span>{String(v)}</span>
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-[11px] italic">Default config</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
