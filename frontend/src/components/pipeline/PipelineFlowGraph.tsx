import { useNavigate } from 'react-router-dom';
import type { PipelineGraph, PipelineNode } from '@/types/pipeline.types';
import {
  Activity,
  BarChart2,
  BrainCircuit,
  CheckCircle2,
  Database,
  FlaskConical,
  Package,
  Play,
  TrendingUp,
} from 'lucide-react';

const ICON_MAP: Record<string, React.ElementType> = {
  Database: Database,
  FlaskConical: FlaskConical,
  Play: Play,
  BrainCircuit: BrainCircuit,
  BarChart2: BarChart2,
  Package: Package,
  TrendingUp: TrendingUp,
  CheckCircle2: CheckCircle2,
  Activity: Activity,
};

const STATUS_CONFIG: Record<string, { border: string; bg: string; iconColor: string; label: string }> = {
  completed: { border: '#22c55e',  bg: '#22c55e15', iconColor: '#22c55e',  label: 'Completed' },
  running:   { border: '#3b82f6',  bg: '#3b82f615', iconColor: '#3b82f6',  label: 'Running'   },
  failed:    { border: '#ef4444',  bg: '#ef444415', iconColor: '#ef4444',  label: 'Failed'    },
  queued:    { border: '#f59e0b',  bg: '#f59e0b15', iconColor: '#f59e0b',  label: 'Queued'    },
  pending:   { border: 'var(--border)', bg: 'var(--bg-secondary)', iconColor: 'var(--text-muted)', label: 'Pending' },
  skipped:   { border: 'var(--border)', bg: 'var(--bg-secondary)', iconColor: 'var(--text-muted)', label: 'Skipped' },
  draft:     { border: 'var(--border)', bg: 'var(--bg-secondary)', iconColor: 'var(--text-muted)', label: 'Draft'   },
  cancelled: { border: '#6b7280',  bg: '#6b728015', iconColor: '#6b7280',  label: 'Cancelled' },
};

function NodeCard({ node, onClick }: { node: PipelineNode; onClick?: () => void }) {
  const cfg = STATUS_CONFIG[node.status] ?? STATUS_CONFIG.pending;
  const Icon = ICON_MAP[node.icon] ?? Activity;
  const isClickable = !!node.link;

  return (
    <div
      onClick={isClickable ? onClick : undefined}
      style={{
        width: 220,
        background: cfg.bg,
        border: `1.5px solid ${cfg.border}`,
        borderRadius: '0.875rem',
        padding: '1rem 1.25rem',
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'transform 0.15s, box-shadow 0.15s',
        position: 'relative',
        boxShadow: node.status === 'running' ? `0 0 12px ${cfg.border}40` : undefined,
      }}
      onMouseEnter={e => {
        if (isClickable) {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
          (e.currentTarget as HTMLElement).style.boxShadow = `0 4px 20px ${cfg.border}30`;
        }
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.transform = '';
        (e.currentTarget as HTMLElement).style.boxShadow = node.status === 'running' ? `0 0 12px ${cfg.border}40` : '';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <div style={{
          width: 36, height: 36, borderRadius: '0.5rem',
          background: `${cfg.border}20`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Icon size={18} style={{ color: cfg.iconColor }} />
        </div>
        <div>
          <p style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', margin: 0 }}>
            {node.label}
          </p>
          <span style={{
            fontSize: '0.68rem', fontWeight: 600, color: cfg.iconColor,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Detail snippets */}
      {node.detail != null && (() => {
        const d = node.detail!;
        if (node.stage_type === 'dataset' && d.rows != null)
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{String(d.rows)} rows · {String(d.columns ?? 0)} cols</div>;
        if (node.stage_type === 'run' && d.model != null)
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Model: {String(d.model)}</div>;
        if (node.stage_type === 'training' && d.duration_seconds != null)
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Duration: {String(d.duration_seconds)}s</div>;
        if (node.stage_type === 'evaluation' && d.accuracy != null)
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Acc: {(Number(d.accuracy) * 100).toFixed(2)}% · F1: {(Number(d.f1_score ?? 0) * 100).toFixed(2)}%</div>;
        if (node.stage_type === 'artifacts')
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{String(d.count ?? 0)} artifact(s)</div>;
        if (node.stage_type === 'metrics' && d.accuracy != null)
          return <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Acc: {(Number(d.accuracy) * 100).toFixed(2)}%</div>;
        return null;
      })()}

      {/* Timestamp */}
      {node.completed_at && (
        <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.4rem', opacity: 0.7 }}>
          {new Date(node.completed_at).toLocaleTimeString()}
        </p>
      )}

      {/* Running pulse indicator */}
      {node.status === 'running' && (
        <span style={{
          position: 'absolute', top: 10, right: 10,
          width: 8, height: 8, borderRadius: '50%',
          background: '#3b82f6', animation: 'pulse 1.5s infinite',
        }} />
      )}
    </div>
  );
}

function ConnectorArrow({ active, isLast }: { active: boolean; isLast: boolean }) {
  if (isLast) return null;
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      gap: 0, padding: '0.25rem 0',
    }}>
      <div style={{
        width: 2, height: 28,
        background: active
          ? 'linear-gradient(to bottom, #22c55e80, #22c55e40)'
          : 'var(--border)',
        borderRadius: 1,
      }} />
      <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
        <path d="M6 8L0 0H12L6 8Z" fill={active ? '#22c55e60' : 'var(--border)'} />
      </svg>
    </div>
  );
}

interface Props {
  graph: PipelineGraph;
}

export function PipelineFlowGraph({ graph }: Props) {
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem 0 0.5rem' }}>
      {/* Run Header */}
      <div style={{
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: '0.75rem', padding: '0.75rem 1.5rem',
        marginBottom: '1.5rem', textAlign: 'center',
      }}>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Execution Graph
        </p>
        <p style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1rem', margin: '0.2rem 0 0' }}>
          {graph.experiment_name} — Run #{graph.run_number}
        </p>
        {graph.dataset_name && (
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0.15rem 0 0' }}>
            Dataset: {graph.dataset_name}
          </p>
        )}
      </div>

      {/* Nodes + Connectors */}
      {graph.nodes.map((node, i) => {
        const edge = graph.edges[i];
        const isLast = i === graph.nodes.length - 1;
        return (
          <div key={node.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <NodeCard
              node={node}
              onClick={node.link ? () => navigate(node.link!) : undefined}
            />
            {!isLast && edge && (
              <ConnectorArrow active={edge.active} isLast={false} />
            )}
          </div>
        );
      })}
    </div>
  );
}
