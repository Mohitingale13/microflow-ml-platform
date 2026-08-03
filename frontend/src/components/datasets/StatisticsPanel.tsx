import { useMemo } from 'react';
import type { DatasetStatistics, NumericColumnStat, CategoricalColumnStat } from '../../types/dataset.types';

interface StatisticsPanelProps {
  stats: DatasetStatistics;
}

export function StatisticsPanel({ stats }: StatisticsPanelProps) {
  const numericStats = useMemo(() => {
    return Object.entries(stats.statistics)
      .filter(([_, stat]) => stat.type === 'numeric')
      .map(([col, stat]) => ({ col, stat: stat as NumericColumnStat }));
  }, [stats]);

  const categoricalStats = useMemo(() => {
    return Object.entries(stats.statistics)
      .filter(([_, stat]) => stat.type === 'categorical')
      .map(([col, stat]) => ({ col, stat: stat as CategoricalColumnStat }));
  }, [stats]);

  const formatNum = (num: number | null) => {
    if (num === null || num === undefined) return 'N/A';
    return Number.isInteger(num) ? num.toLocaleString() : num.toFixed(4);
  };

  return (
    <div className="space-y-8">
      {numericStats.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4 border-b border-border pb-2">
            Numeric Columns ({numericStats.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {numericStats.map(({ col, stat }) => (
              <div key={col} className="bg-surface border border-border rounded-lg p-4 shadow-sm hover:border-accent-blue transition-colors">
                <h4 className="font-medium text-text-primary mb-3 truncate" title={col}>{col}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-text-muted">Mean</span>
                    <span className="text-text-primary font-mono">{formatNum(stat.mean)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Median</span>
                    <span className="text-text-primary font-mono">{formatNum(stat.median)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Std Dev</span>
                    <span className="text-text-primary font-mono">{formatNum(stat.std)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Min</span>
                    <span className="text-text-primary font-mono">{formatNum(stat.min)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Max</span>
                    <span className="text-text-primary font-mono">{formatNum(stat.max)}</span>
                  </div>
                  <div className="flex justify-between mt-2 pt-2 border-t border-border">
                    <span className="text-text-muted">Missing</span>
                    <span className={`font-mono ${stat.missing_count > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {stat.missing_count.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {categoricalStats.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4 border-b border-border pb-2">
            Categorical Columns ({categoricalStats.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {categoricalStats.map(({ col, stat }) => (
              <div key={col} className="bg-surface border border-border rounded-lg p-4 shadow-sm hover:border-accent-blue transition-colors">
                <h4 className="font-medium text-text-primary mb-3 truncate" title={col}>{col}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-text-muted">Unique Vals</span>
                    <span className="text-text-primary font-mono">{stat.unique_values.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Top Value</span>
                    <span className="text-text-primary font-mono truncate max-w-[120px]" title={stat.most_frequent || ''}>
                      {stat.most_frequent || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between mt-2 pt-2 border-t border-border">
                    <span className="text-text-muted">Missing</span>
                    <span className={`font-mono ${stat.missing_count > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {stat.missing_count.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
