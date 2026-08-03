import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { LineageDataset, LineageExperiment, LineageRun } from '@/types/pipeline.types';
import {
  ChevronDown,
  ChevronRight,
  Database,
  FlaskConical,
  Package,
  Play,
} from 'lucide-react';

const STATUS_COLOR: Record<string, string> = {
  completed: '#22c55e',
  active:    '#3b82f6',
  failed:    '#ef4444',
  running:   '#3b82f6',
  queued:    '#f59e0b',
  draft:     '#6b7280',
  archived:  '#6b7280',
};

function StatusDot({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? '#6b7280';
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
      background: color, flexShrink: 0,
    }} />
  );
}

function ArtifactItem({ type, filename }: { type: string; filename: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.5rem',
      padding: '0.3rem 0.6rem',
      background: 'var(--bg-secondary)', borderRadius: '0.375rem',
      border: '1px solid var(--border)',
      fontSize: '0.72rem', color: 'var(--text-muted)',
    }}>
      <Package size={11} style={{ color: '#f59e0b', flexShrink: 0 }} />
      <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>
        {type.replace(/_/g, ' ')}
      </span>
      <span style={{ opacity: 0.6 }}>·</span>
      <span>{filename}</span>
    </div>
  );
}

function RunNode({ run }: { run: LineageRun }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const hasArtifacts = run.artifacts.length > 0;

  return (
    <div style={{ marginTop: '0.5rem' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.45rem 0.75rem',
        borderRadius: '0.5rem',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
        onClick={() => hasArtifacts && setExpanded(e => !e)}
        onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'}
        onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'}
      >
        {hasArtifacts ? (
          expanded ? <ChevronDown size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                   : <ChevronRight size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        ) : (
          <span style={{ width: 13 }} />
        )}

        <Play size={13} style={{ color: '#3b82f6', flexShrink: 0 }} />
        <StatusDot status={run.status} />

        <button
          onClick={e => { e.stopPropagation(); navigate(`/runs/${run.run_id}`); }}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--accent)', fontWeight: 600, fontSize: '0.8rem', padding: 0,
          }}
        >
          Run #{run.run_number}
        </button>

        {run.model && (
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'var(--border)', borderRadius: '0.3rem', padding: '0.1rem 0.4rem' }}>
            {run.model.replace(/_/g, ' ')}
          </span>
        )}

        {hasArtifacts && (
          <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {run.artifacts.length} artifact{run.artifacts.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {expanded && hasArtifacts && (
        <div style={{
          marginLeft: '1.75rem', marginTop: '0.4rem',
          display: 'flex', flexDirection: 'column', gap: '0.3rem',
          paddingLeft: '0.75rem',
          borderLeft: '2px solid var(--border)',
        }}>
          {run.artifacts.map(a => (
            <ArtifactItem key={a.artifact_id} type={a.artifact_type} filename={a.filename} />
          ))}
        </div>
      )}
    </div>
  );
}

function ExperimentNode({ exp }: { exp: LineageExperiment }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(true);

  return (
    <div style={{ marginTop: '0.6rem' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.5rem 0.875rem',
        borderRadius: '0.625rem',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
        onClick={() => setExpanded(e => !e)}
        onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = '#3b82f680'}
        onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'}
      >
        {expanded
          ? <ChevronDown size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          : <ChevronRight size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        }
        <FlaskConical size={14} style={{ color: '#3b82f6', flexShrink: 0 }} />
        <StatusDot status={exp.status} />
        <button
          onClick={e => { e.stopPropagation(); navigate(`/experiments/${exp.experiment_id}`); }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.85rem', padding: 0 }}
        >
          {exp.experiment_name}
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {exp.completed_runs}/{exp.total_runs} completed
        </span>
      </div>

      {expanded && exp.runs.length > 0 && (
        <div style={{
          marginLeft: '1.75rem', paddingLeft: '0.875rem',
          borderLeft: '2px solid var(--border)',
        }}>
          {exp.runs.map(run => (
            <RunNode key={run.run_id} run={run} />
          ))}
        </div>
      )}

      {expanded && exp.runs.length === 0 && (
        <div style={{
          marginLeft: '2.5rem', padding: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic',
        }}>
          No runs yet
        </div>
      )}
    </div>
  );
}

function DatasetNode({ dataset }: { dataset: LineageDataset }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1rem' }}>
      {/* Dataset Header */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: '0.75rem',
          padding: '1rem 1.25rem',
          background: 'var(--bg-secondary)',
          borderBottom: expanded ? '1px solid var(--border)' : 'none',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(e => !e)}
      >
        {expanded
          ? <ChevronDown size={15} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          : <ChevronRight size={15} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        }
        <Database size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <button
            onClick={e => { e.stopPropagation(); navigate(`/datasets/${dataset.dataset_id}`); }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.95rem', padding: 0 }}
          >
            {dataset.dataset_name}
          </button>
          {dataset.row_count != null && (
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
              {dataset.row_count} rows · {dataset.column_count} cols
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>{dataset.total_experiments} exp</span>
          <span>·</span>
          <span>{dataset.total_runs} runs</span>
        </div>
      </div>

      {/* Experiments */}
      {expanded && (
        <div style={{ padding: '0.75rem 1.25rem 1rem' }}>
          {dataset.experiments.length === 0 ? (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No experiments yet
            </p>
          ) : (
            dataset.experiments.map(exp => (
              <ExperimentNode key={exp.experiment_id} exp={exp} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

interface Props {
  datasets: LineageDataset[];
}

export function DatasetLineage({ datasets }: Props) {
  if (datasets.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        <Database size={48} style={{ opacity: 0.2, marginBottom: '0.75rem' }} />
        <p>No datasets found. Upload a dataset to see lineage.</p>
      </div>
    );
  }

  return (
    <div>
      {datasets.map(ds => (
        <DatasetNode key={ds.dataset_id} dataset={ds} />
      ))}
    </div>
  );
}
