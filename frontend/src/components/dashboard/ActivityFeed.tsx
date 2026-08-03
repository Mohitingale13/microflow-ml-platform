/**
 * ActivityFeed.tsx — Chronological platform activity timeline, newest first.
 */

import { formatRelativeTime } from '@/utils/time';
import {
  Database,
  FlaskConical,
  Play,
  CheckCircle2,
  XCircle,
  Archive,
  BarChart3,
  Clock,
  Activity,
} from 'lucide-react';
import type { ActivityItem, ActivityEventType } from '@/types/dashboard.types';
import { useNavigate } from 'react-router-dom';

interface ActivityFeedProps {
  events: ActivityItem[];
  isLoading: boolean;
}

interface EventConfig {
  icon: React.ReactNode;
  color: string;
  badgeColor: string;
}

const EVENT_CONFIG: Record<ActivityEventType, EventConfig> = {
  dataset_uploaded: {
    icon: <Database size={14} />,
    color: 'var(--color-accent-blue)',
    badgeColor: 'rgba(59,130,246,0.15)',
  },
  experiment_created: {
    icon: <FlaskConical size={14} />,
    color: 'var(--color-accent-purple)',
    badgeColor: 'rgba(139,92,246,0.15)',
  },
  run_created: {
    icon: <Play size={14} />,
    color: 'var(--color-text-secondary)',
    badgeColor: 'rgba(139,152,180,0.12)',
  },
  run_queued: {
    icon: <Clock size={14} />,
    color: 'var(--color-accent-cyan)',
    badgeColor: 'rgba(6,182,212,0.12)',
  },
  run_completed: {
    icon: <CheckCircle2 size={14} />,
    color: 'var(--color-accent-emerald)',
    badgeColor: 'rgba(16,185,129,0.15)',
  },
  run_failed: {
    icon: <XCircle size={14} />,
    color: 'var(--color-accent-red)',
    badgeColor: 'rgba(239,68,68,0.15)',
  },
  artifact_generated: {
    icon: <Archive size={14} />,
    color: 'var(--color-accent-purple)',
    badgeColor: 'rgba(139,92,246,0.12)',
  },
  metrics_persisted: {
    icon: <BarChart3 size={14} />,
    color: 'var(--color-accent-cyan)',
    badgeColor: 'rgba(6,182,212,0.12)',
  },
};

function getNavigationPath(event: ActivityItem): string | null {
  switch (event.entity_type) {
    case 'dataset': return `/datasets/${event.entity_id}`;
    case 'experiment': return `/experiments/${event.entity_id}`;
    case 'run': return `/runs/${event.entity_id}`;
    case 'artifact': return `/artifacts`;
    case 'result': return event.metadata?.run_id ? `/runs/${event.metadata.run_id}` : null;
    default: return null;
  }
}

function ActivityEventRow({ event }: { event: ActivityItem }) {
  const navigate = useNavigate();
  const cfg = EVENT_CONFIG[event.event_type] ?? EVENT_CONFIG.run_created;
  const navPath = getNavigationPath(event);

  return (
    <div
      className={`flex items-start gap-3 py-3 border-b border-[var(--color-border)] last:border-0 ${navPath ? 'cursor-pointer hover:bg-surface-2/50 -mx-2 px-2 rounded transition-colors' : ''}`}
      onClick={() => navPath && navigate(navPath)}
    >
      {/* Icon dot */}
      <div
        className="mt-0.5 flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center"
        style={{ background: cfg.badgeColor, color: cfg.color }}
      >
        {cfg.icon}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary leading-tight truncate">
          {event.description}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatRelativeTime(event.occurred_at)}
        </p>
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-[var(--color-border)] last:border-0 animate-pulse">
      <div className="w-7 h-7 rounded-full bg-surface-2 flex-shrink-0 mt-0.5" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 bg-surface-2 rounded w-3/4" />
        <div className="h-3 bg-surface-2 rounded w-24" />
      </div>
    </div>
  );
}

export function ActivityFeed({ events, isLoading }: ActivityFeedProps) {
  return (
    <div className="card p-5">
      <h3 className="section-title mb-1 flex items-center gap-2">
        <Activity size={16} className="text-accent-cyan" />
        Recent Activity
      </h3>
      <p className="text-xs text-muted-foreground mb-4">Platform events in real time, newest first</p>

      <div>
        {isLoading && Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}

        {!isLoading && events.length === 0 && (
          <div className="py-8 text-center text-muted-foreground text-sm">
            <Activity size={32} className="mx-auto mb-2 opacity-30" />
            No activity yet. Upload a dataset to get started.
          </div>
        )}

        {!isLoading && events.map((event, i) => (
          <ActivityEventRow key={`${event.entity_id}-${event.event_type}-${i}`} event={event} />
        ))}
      </div>
    </div>
  );
}
