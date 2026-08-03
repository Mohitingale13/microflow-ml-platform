/**
 * MetricsCharts.tsx — Visual charts using Recharts for historical experiment analytics.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import type {
  ExperimentMetricSummary,
  MetricsOverview,
  ModelMetricSummary,
} from '@/types/metrics.types';

interface MetricsChartsProps {
  overview?: MetricsOverview;
  modelMetrics: ModelMetricSummary[];
  experimentMetrics: ExperimentMetricSummary[];
}

const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];
const STATUS_COLORS = {
  completed: '#10b981',
  failed: '#ef4444',
  other: '#64748b',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 backdrop-blur-md border border-border px-3 py-2 rounded-lg shadow-xl text-xs">
        <p className="font-semibold text-foreground mb-1">{label || payload[0]?.name}</p>
        {payload.map((entry: any, index: number) => (
          <div key={`item-${index}`} className="flex items-center gap-2 text-muted-foreground my-0.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
            <span>{entry.name}:</span>
            <span className="font-mono font-medium text-foreground">
              {typeof entry.value === 'number'
                ? entry.value < 1 && entry.value > 0
                  ? `${(entry.value * 100).toFixed(2)}%`
                  : entry.value.toFixed(2)
                : entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function MetricsCharts({
  overview,
  modelMetrics,
  experimentMetrics,
}: MetricsChartsProps) {
  // Chart 1: Accuracy by Model Data
  const accuracyByModelData = modelMetrics.map((m) => ({
    name: m.model_type.replace(/_/g, ' ').toUpperCase(),
    'Best Accuracy': m.best_accuracy ? Number((m.best_accuracy * 100).toFixed(2)) : 0,
    'Avg Accuracy': m.average_accuracy ? Number((m.average_accuracy * 100).toFixed(2)) : 0,
  }));

  // Chart 2: Runs per Model Data
  const runsPerModelData = modelMetrics
    .filter((m) => m.number_of_runs > 0)
    .map((m) => ({
      name: m.model_type.replace(/_/g, ' ').toUpperCase(),
      value: m.number_of_runs,
    }));

  // Chart 3: Avg Accuracy by Experiment Data
  const accuracyByExpData = experimentMetrics
    .filter((e) => e.average_accuracy !== null)
    .slice(0, 8)
    .map((e) => ({
      name: e.experiment_name.length > 18 ? `${e.experiment_name.substring(0, 16)}...` : e.experiment_name,
      fullName: e.experiment_name,
      'Avg Accuracy (%)': Number(((e.average_accuracy || 0) * 100).toFixed(2)),
    }));

  // Chart 4: Training Duration Distribution Data
  const durationByModelData = modelMetrics.map((m) => ({
    name: m.model_type.replace(/_/g, ' ').toUpperCase(),
    'Avg Duration (s)': m.average_duration || 0,
  }));

  // Chart 5: Success vs Failed Runs Data
  const otherRuns = overview
    ? Math.max(0, overview.total_runs - overview.completed_runs - overview.failed_runs)
    : 0;

  const runStatusData = [
    { name: 'Completed', value: overview?.completed_runs || 0, color: STATUS_COLORS.completed },
    { name: 'Failed', value: overview?.failed_runs || 0, color: STATUS_COLORS.failed },
    ...(otherRuns > 0 ? [{ name: 'Other/Active', value: otherRuns, color: STATUS_COLORS.other }] : []),
  ].filter((d) => d.value > 0);

  const hasData = modelMetrics.length > 0 || (overview && overview.total_runs > 0);

  if (!hasData) {
    return (
      <div className="card p-8 text-center text-muted-foreground border-dashed">
        <p className="text-sm">No historical execution data available to plot charts.</p>
        <p className="text-xs text-muted-foreground/70 mt-1">Execute training runs to see visual analytics.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 1. Accuracy by Model */}
      <div className="card p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-foreground">1. Accuracy by Model</h3>
          <p className="text-xs text-muted-foreground">Best vs. Average accuracy percentage per model</p>
        </div>
        <div className="h-64 w-full">
          {accuracyByModelData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={accuracyByModelData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="Best Accuracy" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Avg Accuracy" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
              No completed model runs
            </div>
          )}
        </div>
      </div>

      {/* 2. Runs per Model */}
      <div className="card p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-foreground">2. Runs per Model</h3>
          <p className="text-xs text-muted-foreground">Distribution of completed training runs by model family</p>
        </div>
        <div className="h-64 w-full flex items-center justify-center">
          {runsPerModelData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={runsPerModelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                  labelLine={false}
                >
                  {runsPerModelData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
              No runs recorded
            </div>
          )}
        </div>
      </div>

      {/* 3. Average Accuracy by Experiment */}
      <div className="card p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-foreground">3. Average Accuracy by Experiment</h3>
          <p className="text-xs text-muted-foreground">Mean classification performance across experiment tracks</p>
        </div>
        <div className="h-64 w-full">
          {accuracyByExpData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={accuracyByExpData} margin={{ top: 10, right: 10, left: -20, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={10}
                  angle={-20}
                  textAnchor="end"
                  interval={0}
                  tickLine={false}
                />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Avg Accuracy (%)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
              No experiment metrics available
            </div>
          )}
        </div>
      </div>

      {/* 4. Training Duration Distribution & 5. Success vs Failed */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 4. Duration */}
        <div className="card p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">
              4. Duration by Model
            </h3>
            <p className="text-[11px] text-muted-foreground mb-2">Average execution time (seconds)</p>
          </div>
          <div className="h-48 w-full">
            {durationByModelData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={durationByModelData} margin={{ top: 5, right: 5, left: -25, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={9} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={9} unit="s" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="Avg Duration (s)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                No timing data
              </div>
            )}
          </div>
        </div>

        {/* 5. Success vs Failed */}
        <div className="card p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">
              5. Success vs Failed
            </h3>
            <p className="text-[11px] text-muted-foreground mb-2">Execution outcome breakdown</p>
          </div>
          <div className="h-48 w-full flex items-center justify-center">
            {runStatusData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={runStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={60}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {runStatusData.map((entry, index) => (
                      <Cell key={`status-cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                No runs executed
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
