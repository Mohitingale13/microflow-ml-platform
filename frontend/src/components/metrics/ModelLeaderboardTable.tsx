/**
 * ModelLeaderboardTable.tsx — Sortable model leaderboard table.
 */

import { useState, useMemo } from 'react';
import { ArrowUpDown, Award, Cpu } from 'lucide-react';
import type { ModelMetricSummary } from '@/types/metrics.types';

interface ModelLeaderboardTableProps {
  models: ModelMetricSummary[];
  isLoading: boolean;
}

type SortField =
  | 'best_accuracy'
  | 'average_accuracy'
  | 'best_f1'
  | 'average_f1'
  | 'average_roc_auc'
  | 'average_duration'
  | 'number_of_runs';

export function ModelLeaderboardTable({ models, isLoading }: ModelLeaderboardTableProps) {
  const [sortField, setSortField] = useState<SortField>('best_accuracy');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedModels = useMemo(() => {
    return [...models].sort((a, b) => {
      const valA = a[sortField] ?? -Infinity;
      const valB = b[sortField] ?? -Infinity;
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [models, sortField, sortAsc]);

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

  if (models.length === 0) {
    return (
      <div className="card p-8 text-center text-muted-foreground border-dashed">
        <Cpu className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm font-medium">No model metrics available yet</p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Execute and complete runs to view the model leaderboard.
        </p>
      </div>
    );
  }

  const renderSortHeader = (label: string, field: SortField) => (
    <button
      onClick={() => handleSort(field)}
      className="inline-flex items-center gap-1 hover:text-foreground transition-colors font-medium text-xs uppercase tracking-wider"
    >
      <span>{label}</span>
      <ArrowUpDown size={12} className={sortField === field ? 'text-primary' : 'text-muted-foreground/50'} />
    </button>
  );

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Award size={16} className="text-amber-400" />
            Model Leaderboard
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Ranked performance benchmarks across model algorithms
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground bg-muted/50 px-2.5 py-1 rounded">
          {models.length} {models.length === 1 ? 'model' : 'models'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/40 border-b border-border text-muted-foreground">
            <tr>
              <th className="py-3 px-4 w-12 text-center">Rank</th>
              <th className="py-3 px-4">Model</th>
              <th className="py-3 px-4 text-center">{renderSortHeader('Runs', 'number_of_runs')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Best Acc', 'best_accuracy')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Avg Acc', 'average_accuracy')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Best F1', 'best_f1')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Avg F1', 'average_f1')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Avg ROC', 'average_roc_auc')}</th>
              <th className="py-3 px-4 text-right">{renderSortHeader('Avg Duration', 'average_duration')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sortedModels.map((m, index) => {
              const rank = index + 1;
              const formattedName = m.model_type.replace(/_/g, ' ').toUpperCase();

              return (
                <tr key={m.model_type} className="hover:bg-muted/30 transition-colors">
                  <td className="py-3.5 px-4 text-center font-mono font-medium">
                    {rank === 1 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-400/20 text-amber-300 font-bold">
                        1
                      </span>
                    ) : rank === 2 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-300/20 text-slate-200 font-bold">
                        2
                      </span>
                    ) : rank === 3 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-700/20 text-amber-500 font-bold">
                        3
                      </span>
                    ) : (
                      <span className="text-muted-foreground">{rank}</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-medium text-foreground">
                    <span className="font-mono bg-muted/60 px-2 py-0.5 rounded text-xs">
                      {formattedName}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono text-muted-foreground">
                    {m.number_of_runs}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-emerald-400">
                    {m.best_accuracy !== null ? `${(m.best_accuracy * 100).toFixed(2)}%` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-foreground">
                    {m.average_accuracy !== null ? `${(m.average_accuracy * 100).toFixed(2)}%` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-purple-400">
                    {m.best_f1 !== null ? `${(m.best_f1 * 100).toFixed(2)}%` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-foreground">
                    {m.average_f1 !== null ? `${(m.average_f1 * 100).toFixed(2)}%` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-cyan-400">
                    {m.average_roc_auc !== null ? m.average_roc_auc.toFixed(4) : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">
                    {m.average_duration !== null ? `${m.average_duration.toFixed(2)}s` : '—'}
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
