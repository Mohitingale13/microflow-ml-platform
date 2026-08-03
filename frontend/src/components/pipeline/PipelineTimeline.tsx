import type { PipelineTimeline, TimelineEvent } from '@/types/pipeline.types';
import {
  Activity,
  BarChart2,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Database,
  FlaskConical,
  Package,
  Play,
  TrendingUp,
  XCircle,
} from 'lucide-react';

const STAGE_ICONS: Record<string, React.ElementType> = {
  dataset:    Database,
  experiment: FlaskConical,
  run:        Play,
  training:   BrainCircuit,
  evaluation: BarChart2,
  artifacts:  Package,
  metrics:    TrendingUp,
  completed:  CheckCircle2,
};

const STATUS_COLOR: Record<string, string> = {
  completed: '#22c55e',
  running:   '#3b82f6',
  failed:    '#ef4444',
  pending:   'var(--border-color, #374151)',
  skipped:   '#6b7280',
};

function EventRow({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const Icon = STAGE_ICONS[event.stage_type] ?? Activity;
  const color = STATUS_COLOR[event.status] ?? STATUS_COLOR.pending;
  const isPending = event.status === 'pending' || event.status === 'skipped';

  return (
    <div style={{ display: 'flex', gap: '1rem', opacity: isPending ? 0.45 : 1 }}>
      {/* Left timeline rail */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: 36 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: `${color}20`,
          border: `2px solid ${color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: event.status === 'running' ? `0 0 10px ${color}50` : undefined,
        }}>
          {event.status === 'failed'
            ? <XCircle size={16} style={{ color }} />
            : <Icon size={16} style={{ color }} />
          }
        </div>
        {!isLast && (
          <div style={{
            flex: 1, width: 2, marginTop: 4,
            background: event.status === 'completed'
              ? `linear-gradient(to bottom, ${color}60, var(--border))`
              : 'var(--border)',
            borderRadius: 1,
            minHeight: 24,
          }} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingBottom: isLast ? 0 : '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: '0.5rem' }}>
          <p style={{
            fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', margin: 0,
          }}>
            {event.event}
          </p>
          {event.duration_seconds != null && (
            <span style={{
              display: 'flex', alignItems: 'center', gap: '0.3rem',
              fontSize: '0.72rem', color: 'var(--text-muted)',
              background: 'var(--bg-secondary)', borderRadius: '0.375rem',
              padding: '0.15rem 0.5rem',
            }}>
              <Clock size={10} />
              {event.duration_seconds.toFixed(1)}s
            </span>
          )}
        </div>

        {event.timestamp && (
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '0.15rem 0 0' }}>
            {new Date(event.timestamp).toLocaleString()}
          </p>
        )}

        {event.detail && (
          <p style={{
            fontSize: '0.78rem', color: 'var(--text-secondary)',
            margin: '0.35rem 0 0',
            background: 'var(--bg-secondary)',
            borderRadius: '0.375rem',
            padding: '0.3rem 0.6rem',
            borderLeft: `3px solid ${color}50`,
          }}>
            {event.detail}
          </p>
        )}
      </div>
    </div>
  );
}

interface Props {
  timeline: PipelineTimeline;
}

export function PipelineTimelineComponent({ timeline }: Props) {
  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '1.25rem',
      }}>
        <div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Execution Timeline
          </p>
          <p style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0.2rem 0 0' }}>
            Run #{timeline.run_number} · {timeline.experiment_name}
          </p>
        </div>
        {timeline.total_duration_seconds != null && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            background: 'var(--bg-secondary)', border: '1px solid var(--border)',
            borderRadius: '0.5rem', padding: '0.4rem 0.875rem',
            fontSize: '0.82rem', color: 'var(--text-secondary)',
          }}>
            <Clock size={14} style={{ color: 'var(--accent)' }} />
            Total: <strong style={{ color: 'var(--text-primary)' }}>{timeline.total_duration_seconds.toFixed(2)}s</strong>
          </div>
        )}
      </div>

      {/* Timeline events */}
      <div>
        {timeline.events.map((event, i) => (
          <EventRow key={`${event.order}-${event.stage_type}`} event={event} isLast={i === timeline.events.length - 1} />
        ))}
      </div>
    </div>
  );
}
