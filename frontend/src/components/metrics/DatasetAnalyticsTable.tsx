/**
 * DatasetAnalyticsTable.tsx — Dataset-level metrics & best model summary table.
 */

import { Link } from 'react-router-dom';
import { Database, ExternalLink } from 'lucide-react';
import type { DatasetMetricSummary } from '@/types/metrics.types';

interface DatasetAnalyticsTableProps {
  datasets: DatasetMetricSummary[];
  isLoading: boolean;
}

export function DatasetAnalyticsTable({
  datasets,
  isLoading,
}: DatasetAnalyticsTableProps) {
  if (isLoading) {
    return (
      <div className="card p-6 animate-pulse">
        <div className="h-6 bg-muted/60 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-10 bg-muted/40 rounded w-full"></div>
          ))}
        </div>
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="card p-8 text-center text-muted-foreground border-dashed">
        <Database className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm font-medium">No datasets found</p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Upload datasets and train models to see analytics.
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Database size={16} className="text-primary" />
            Dataset Analytics
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Performance comparison and best model achievements per dataset
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground bg-muted/50 px-2.5 py-1 rounded">
          {datasets.length} {datasets.length === 1 ? 'dataset' : 'datasets'}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/40 border-b border-border text-muted-foreground">
            <tr>
              <th className="py-3 px-4">Dataset</th>
              <th className="py-3 px-4 text-center">Experiments</th>
              <th className="py-3 px-4 text-center">Total Runs</th>
              <th className="py-3 px-4">Best Model</th>
              <th className="py-3 px-4 text-right">Top Accuracy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {datasets.map((ds) => (
              <tr key={ds.dataset_id} className="hover:bg-muted/30 transition-colors">
                {/* Dataset Link */}
                <td className="py-3.5 px-4 font-medium text-foreground">
                  <Link
                    to={`/datasets/${ds.dataset_id}`}
                    className="hover:text-primary transition-colors inline-flex items-center gap-1.5 font-medium"
                  >
                    <span>{ds.dataset_name}</span>
                    <ExternalLink size={11} className="text-muted-foreground opacity-50" />
                  </Link>
                </td>

                {/* Experiments Count */}
                <td className="py-3.5 px-4 text-center font-mono text-foreground">
                  {ds.number_of_experiments}
                </td>

                {/* Runs Count */}
                <td className="py-3.5 px-4 text-center font-mono text-foreground font-medium">
                  {ds.number_of_runs}
                </td>

                {/* Best Model */}
                <td className="py-3.5 px-4">
                  {ds.best_model ? (
                    <span className="font-mono bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-xs">
                      {ds.best_model.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>

                {/* Top Accuracy */}
                <td className="py-3.5 px-4 text-right font-mono font-semibold text-emerald-400">
                  {ds.best_accuracy !== null ? `${(ds.best_accuracy * 100).toFixed(2)}%` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
