/**
 * OverviewCards.tsx — 8 stat cards summarising the entire platform.
 */

import { Database, FlaskConical, Play, CheckCircle, XCircle, Archive, Cpu, HardDrive } from 'lucide-react';
import type { DashboardOverview } from '@/types/dashboard.types';

interface OverviewCardsProps {
  overview: DashboardOverview | undefined;
  isLoading: boolean;
}

interface CardDef {
  label: string;
  value: (o: DashboardOverview) => string | number;
  sub: (o: DashboardOverview) => string;
  icon: React.ReactNode;
  accent: string;
  glow: string;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

const CARDS: CardDef[] = [
  {
    label: 'Datasets',
    value: o => o.total_datasets,
    sub: o => o.total_datasets === 1 ? '1 dataset available' : `${o.total_datasets} datasets available`,
    icon: <Database size={20} />,
    accent: 'accent-blue',
    glow: 'var(--shadow-glow-blue)',
  },
  {
    label: 'Experiments',
    value: o => o.total_experiments,
    sub: o => `${o.total_experiments} total experiments`,
    icon: <FlaskConical size={20} />,
    accent: 'accent-purple',
    glow: 'var(--shadow-glow-purple)',
  },
  {
    label: 'Total Runs',
    value: o => o.total_runs,
    sub: o => `${o.running_runs} currently running`,
    icon: <Play size={20} />,
    accent: 'accent-cyan',
    glow: 'var(--shadow-glow-cyan)',
  },
  {
    label: 'Completed',
    value: o => o.completed_runs,
    sub: o => `${(o.success_rate * 100).toFixed(1)}% success rate`,
    icon: <CheckCircle size={20} />,
    accent: 'accent-emerald',
    glow: 'var(--shadow-glow-emerald)',
  },
  {
    label: 'Failed',
    value: o => o.failed_runs,
    sub: o => o.failed_runs === 0 ? 'No failures' : `${o.failed_runs} run${o.failed_runs === 1 ? '' : 's'} failed`,
    icon: <XCircle size={20} />,
    accent: 'accent-red',
    glow: '0 0 24px rgba(239,68,68,0.15)',
  },
  {
    label: 'Artifacts',
    value: o => o.total_artifacts,
    sub: o => `${o.total_artifacts} stored files`,
    icon: <Archive size={20} />,
    accent: 'accent-purple',
    glow: 'var(--shadow-glow-purple)',
  },
  {
    label: 'Models Stored',
    value: o => o.models_stored,
    sub: o => o.average_accuracy != null ? `Avg accuracy: ${(o.average_accuracy * 100).toFixed(1)}%` : 'No results yet',
    icon: <Cpu size={20} />,
    accent: 'accent-cyan',
    glow: 'var(--shadow-glow-cyan)',
  },
  {
    label: 'Storage Used',
    value: o => formatBytes(o.storage_used_bytes),
    sub: o => o.average_training_duration_seconds != null
      ? `Avg train time: ${o.average_training_duration_seconds.toFixed(1)}s`
      : 'Artifact storage total',
    icon: <HardDrive size={20} />,
    accent: 'accent-emerald',
    glow: 'var(--shadow-glow-emerald)',
  },
];

function SkeletonCard() {
  return (
    <div className="stat-card animate-pulse">
      <div className="h-4 bg-surface-2 rounded w-20 mb-3" />
      <div className="h-8 bg-surface-2 rounded w-14 mb-2" />
      <div className="h-3 bg-surface-2 rounded w-28" />
    </div>
  );
}

export function OverviewCards({ overview, isLoading }: OverviewCardsProps) {
  if (isLoading || !overview) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {CARDS.map(card => (
        <div
          key={card.label}
          className={`stat-card ${card.accent}`}
          style={{ boxShadow: card.glow }}
        >
          <div className="flex items-center justify-between mb-2">
            <p className="stat-label">{card.label}</p>
            <span className="text-muted-foreground opacity-60">{card.icon}</span>
          </div>
          <p className="stat-value">{card.value(overview)}</p>
          <p className="stat-desc">{card.sub(overview)}</p>
        </div>
      ))}
    </div>
  );
}
