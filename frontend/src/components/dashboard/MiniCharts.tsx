/**
 * MiniCharts.tsx — Compact platform analytics charts for the dashboard.
 *
 * Uses the same Recharts library already installed. Charts are intentionally
 * compact — they summarise, not duplicate, the full Metrics page.
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { PieChart as PieIcon, BarChart3, TrendingUp } from 'lucide-react';
import type { DashboardOverview } from '@/types/dashboard.types';
import type { ModelMetricSummary } from '@/types/metrics.types';

interface MiniChartsProps {
  overview: DashboardOverview | undefined;
  modelMetrics: ModelMetricSummary[];
  isLoading: boolean;
}

const PALETTE = ['#6366f1', '#10b981', '#ef4444', '#f59e0b', '#06b6d4', '#8b5cf6'];

const TOOLTIP_STYLE = {
  backgroundColor: '#161b2c',
  border: '1px solid #1f2a45',
  borderRadius: '8px',
  fontSize: '12px',
  color: '#e8edf5',
};

// ── Run Status Distribution ───────────────────────────────────────────────────

function RunStatusPie({ overview }: { overview: DashboardOverview }) {
  const data = [
    { name: 'Completed', value: overview.completed_runs },
    { name: 'Failed', value: overview.failed_runs },
    { name: 'Running', value: overview.running_runs },
    { name: 'Other', value: Math.max(0, overview.total_runs - overview.completed_runs - overview.failed_runs - overview.running_runs) },
  ].filter(d => d.value > 0);

  if (data.length === 0) {
    return <EmptyChart label="No runs yet" />;
  }

  const STATUS_COLORS = ['#10b981', '#ef4444', '#06b6d4', '#8b98b4'];

  return (
    <div>
      <h4 className="text-xs font-medium text-text-secondary mb-3 flex items-center gap-1.5">
        <PieIcon size={12} />
        Run Status Distribution
      </h4>
      <ResponsiveContainer width="100%" height={150}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={35}
            outerRadius={60}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={index} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} itemStyle={{ color: '#e8edf5' }} labelStyle={{ color: '#8b98b4' }} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap gap-x-3 gap-y-1 justify-center mt-1">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[i % STATUS_COLORS.length] }} />
            <span className="text-[10px] text-muted-foreground">{d.name}: {d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Model Distribution ────────────────────────────────────────────────────────

function ModelDistributionBar({ modelMetrics }: { modelMetrics: ModelMetricSummary[] }) {
  if (modelMetrics.length === 0) {
    return <EmptyChart label="No completed runs yet" />;
  }

  const data = modelMetrics.map(m => ({
    name: m.model_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).replace('Logistic Regression', 'LR').replace('Random Forest', 'RF'),
    runs: m.number_of_runs,
    acc: m.best_accuracy != null ? Math.round(m.best_accuracy * 100) : 0,
  }));

  return (
    <div>
      <h4 className="text-xs font-medium text-text-secondary mb-3 flex items-center gap-1.5">
        <BarChart3 size={12} />
        Model Performance (Best Accuracy %)
      </h4>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,42,69,0.8)" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8b98b4' }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#8b98b4' }} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            itemStyle={{ color: '#e8edf5' }}
            labelStyle={{ color: '#8b98b4' }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [`${Number(value)}%`, 'Best Accuracy']}
          />
          <Bar dataKey="acc" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Model Run Count ───────────────────────────────────────────────────────────

function ModelRunCountPie({ modelMetrics }: { modelMetrics: ModelMetricSummary[] }) {
  if (modelMetrics.length === 0) {
    return <EmptyChart label="No completed runs yet" />;
  }

  const data = modelMetrics.map(m => ({
    name: m.model_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: m.number_of_runs,
  }));

  return (
    <div>
      <h4 className="text-xs font-medium text-text-secondary mb-3 flex items-center gap-1.5">
        <TrendingUp size={12} />
        Runs by Model Type
      </h4>
      <ResponsiveContainer width="100%" height={150}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={60}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={index} fill={PALETTE[index % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap gap-x-3 gap-y-1 justify-center mt-1">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="text-[10px] text-muted-foreground">{d.name}: {d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-[150px] text-xs text-muted-foreground">
      {label}
    </div>
  );
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function ChartSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-3 bg-surface-2 rounded w-32 mb-3" />
      <div className="h-[150px] bg-surface-2 rounded" />
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────

export function MiniCharts({ overview, modelMetrics, isLoading }: MiniChartsProps) {
  return (
    <div className="card p-5">
      <h3 className="section-title mb-1 flex items-center gap-2">
        <BarChart3 size={16} className="text-accent-cyan" />
        Platform Analytics
      </h3>
      <p className="text-xs text-muted-foreground mb-5">Compact summary — see Metrics page for full analysis</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {isLoading ? (
          <>
            <ChartSkeleton />
            <ChartSkeleton />
            <ChartSkeleton />
          </>
        ) : (
          <>
            {overview && <RunStatusPie overview={overview} />}
            <ModelDistributionBar modelMetrics={modelMetrics} />
            <ModelRunCountPie modelMetrics={modelMetrics} />
          </>
        )}
      </div>
    </div>
  );
}
