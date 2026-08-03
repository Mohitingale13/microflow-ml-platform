import type { RunStatus } from '@/types/experiment.types';

const STATUS_CONFIG: Record<
  RunStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  draft:     { label: 'Draft',     bg: 'bg-surface-2',       text: 'text-text-muted',       dot: 'bg-text-muted' },
  queued:    { label: 'Queued',    bg: 'bg-amber-500/10',    text: 'text-amber-400',         dot: 'bg-amber-400' },
  running:   { label: 'Running',   bg: 'bg-accent-blue/10',  text: 'text-accent-blue',       dot: 'bg-accent-blue animate-pulse' },
  completed: { label: 'Completed', bg: 'bg-accent-emerald/10', text: 'text-accent-emerald', dot: 'bg-accent-emerald' },
  failed:    { label: 'Failed',    bg: 'bg-accent-red/10',   text: 'text-accent-red',        dot: 'bg-accent-red' },
  cancelled: { label: 'Cancelled', bg: 'bg-surface-2',       text: 'text-text-muted',       dot: 'bg-text-muted' },
};

const EXPERIMENT_STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string }
> = {
  draft:    { label: 'Draft',    bg: 'bg-surface-2',           text: 'text-text-muted' },
  active:   { label: 'Active',   bg: 'bg-accent-blue/10',      text: 'text-accent-blue' },
  archived: { label: 'Archived', bg: 'bg-accent-purple/10',    text: 'text-accent-purple' },
};

interface RunStatusBadgeProps {
  status: RunStatus;
  size?: 'sm' | 'md';
}

export function RunStatusBadge({ status, size = 'md' }: RunStatusBadgeProps) {
  const cfg = STATUS_CONFIG[status];
  const sizeClass = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium border border-white/5 ${sizeClass} ${cfg.bg} ${cfg.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

interface ExperimentStatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export function ExperimentStatusBadge({ status, size = 'md' }: ExperimentStatusBadgeProps) {
  const cfg = EXPERIMENT_STATUS_CONFIG[status] ?? EXPERIMENT_STATUS_CONFIG.draft;
  const sizeClass = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium border border-white/5 ${sizeClass} ${cfg.bg} ${cfg.text}`}
    >
      {cfg.label}
    </span>
  );
}
