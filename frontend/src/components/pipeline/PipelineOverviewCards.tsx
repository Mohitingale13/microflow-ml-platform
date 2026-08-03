import {
  Activity,
  Box,
  CheckCircle,
  Clock,
  Package,
  XCircle,
} from 'lucide-react';
import type { PipelineOverview } from '@/types/pipeline.types';

interface Props {
  overview: PipelineOverview;
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  sub?: string;
}) {
  return (
    <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            {label}
          </p>
          <p style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
            {value}
          </p>
          {sub && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>{sub}</p>
          )}
        </div>
        <div style={{
          width: 42,
          height: 42,
          borderRadius: '0.625rem',
          background: `${color}18`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  );
}

export function PipelineOverviewCards({ overview }: Props) {
  const successPct = overview.total_pipelines > 0
    ? `${(overview.success_rate * 100).toFixed(1)}% success`
    : undefined;

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '1.5rem',
    }}>
      <StatCard
        label="Total Pipelines"
        value={overview.total_pipelines}
        icon={Box}
        color="var(--accent)"
        sub={successPct}
      />
      <StatCard
        label="Completed"
        value={overview.completed}
        icon={CheckCircle}
        color="#22c55e"
      />
      <StatCard
        label="Running"
        value={overview.running}
        icon={Activity}
        color="#3b82f6"
      />
      <StatCard
        label="Failed"
        value={overview.failed}
        icon={XCircle}
        color="#ef4444"
      />
      <StatCard
        label="Avg Duration"
        value={overview.average_duration_seconds != null
          ? `${overview.average_duration_seconds.toFixed(1)}s`
          : '—'
        }
        icon={Clock}
        color="#a78bfa"
      />
      <StatCard
        label="Total Artifacts"
        value={overview.total_artifacts_produced}
        icon={Package}
        color="#f59e0b"
      />
    </div>
  );
}
