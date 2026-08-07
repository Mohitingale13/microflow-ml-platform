import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Clock,
  Filter,
  Search,
  Zap,
} from 'lucide-react';
import type { PipelineRunSummary } from '@/types/pipeline.types';
import { formatModelType } from '@/utils/format';
import { formatDate } from '@/utils/format';

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  completed: { bg: '#22c55e20', color: '#22c55e', label: 'Completed' },
  running:   { bg: '#3b82f620', color: '#3b82f6', label: 'Running' },
  failed:    { bg: '#ef444420', color: '#ef4444', label: 'Failed' },
  queued:    { bg: '#f59e0b20', color: '#f59e0b', label: 'Queued' },
  draft:     { bg: 'var(--border)', color: 'var(--text-muted)', label: 'Draft' },
  cancelled: { bg: '#6b728020', color: '#6b7280', label: 'Cancelled' },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
      background: s.bg, color: s.color,
      borderRadius: '9999px', padding: '0.2rem 0.65rem',
      fontSize: '0.72rem', fontWeight: 600,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%', background: s.color,
        animation: status === 'running' ? 'pulse 1.5s infinite' : undefined,
      }} />
      {s.label}
    </span>
  );
}

function formatDuration(sec: number | null): string {
  if (sec == null) return '—';
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const m = Math.floor(sec / 60);
  const s2 = Math.round(sec % 60);
  return `${m}m ${s2}s`;
}

interface Props {
  runs: PipelineRunSummary[];
  onSelectRun: (runId: string) => void;
  selectedRunId?: string;
}

const ALL_STATUSES = ['completed', 'running', 'failed', 'queued', 'draft', 'cancelled'];

export function PipelineRunsTable({ runs, onSelectRun, selectedRunId }: Props) {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterModel, setFilterModel] = useState('');
  const [sortField, setSortField] = useState<string>('started_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Unique models across all runs
  const models = useMemo(() => {
    const set = new Set<string>();
    runs.forEach(r => { if (r.model) set.add(r.model); });
    return Array.from(set);
  }, [runs]);

  const filtered = useMemo(() => {
    let list = runs;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(r =>
        r.run_number.toString().includes(q) ||
        r.experiment_name.toLowerCase().includes(q) ||
        (r.dataset_name ?? '').toLowerCase().includes(q) ||
        (r.model ?? '').toLowerCase().includes(q),
      );
    }
    if (filterStatus) list = list.filter(r => r.status === filterStatus);
    if (filterModel) list = list.filter(r => r.model === filterModel);

    const dir = sortDir === 'asc' ? 1 : -1;
    return [...list].sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sortField] ?? '';
      const bv = (b as unknown as Record<string, unknown>)[sortField] ?? '';
      const as = String(av), bs = String(bv);
      return as < bs ? -dir : as > bs ? dir : 0;
    });
  }, [runs, search, filterStatus, filterModel, sortField, sortDir]);

  function toggleSort(field: string) {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('desc'); }
  }

  function SortIcon({ field }: { field: string }) {
    if (sortField !== field) return <span style={{ opacity: 0.3 }}>↕</span>;
    return <span>{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  const thStyle: React.CSSProperties = {
    padding: '0.75rem 1rem',
    textAlign: 'left',
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  };

  const tdStyle: React.CSSProperties = {
    padding: '0.875rem 1rem',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border)',
    verticalAlign: 'middle',
  };

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 200px', minWidth: 160 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search runs…"
            className="input"
            style={{ width: '100%', paddingLeft: 30, height: 36, fontSize: '0.82rem' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <Filter size={13} />
        </div>

        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="input"
          style={{ height: 36, fontSize: '0.82rem' }}
        >
          <option value="">All Statuses</option>
          {ALL_STATUSES.map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>

        <select
          value={filterModel}
          onChange={e => setFilterModel(e.target.value)}
          className="input"
          style={{ height: 36, fontSize: '0.82rem' }}
        >
          <option value="">All Models</option>
          {models.map(m => (
            <option key={m} value={m}>{formatModelType(m)}</option>
          ))}
        </select>

        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filtered.length} / {runs.length} runs
        </span>
      </div>

      {/* Table */}
      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <Zap size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
            <p>No pipeline runs match your filters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
                  <th style={thStyle} onClick={() => toggleSort('run_number')}>Run <SortIcon field="run_number" /></th>
                  <th style={thStyle} onClick={() => toggleSort('experiment_name')}>Experiment <SortIcon field="experiment_name" /></th>
                  <th style={thStyle}>Dataset</th>
                  <th style={thStyle} onClick={() => toggleSort('model')}>Model <SortIcon field="model" /></th>
                  <th style={thStyle} onClick={() => toggleSort('status')}>Status <SortIcon field="status" /></th>
                  <th style={thStyle} onClick={() => toggleSort('started_at')}>Started <SortIcon field="started_at" /></th>
                  <th style={thStyle} onClick={() => toggleSort('completed_at')}>Completed <SortIcon field="completed_at" /></th>
                  <th style={thStyle} onClick={() => toggleSort('duration_seconds')}>Duration <SortIcon field="duration_seconds" /></th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(run => {
                  const isSelected = run.run_id === selectedRunId;
                  return (
                    <tr
                      key={run.run_id}
                      style={{
                        cursor: 'pointer',
                        background: isSelected ? 'var(--accent)12' : 'transparent',
                        transition: 'background 0.15s',
                        borderLeft: isSelected ? '3px solid var(--accent)' : '3px solid transparent',
                      }}
                      onClick={() => onSelectRun(run.run_id)}
                      onMouseEnter={e => {
                        if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)';
                      }}
                      onMouseLeave={e => {
                        if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'transparent';
                      }}
                    >
                      <td style={{ ...tdStyle, color: 'var(--text-primary)', fontWeight: 600 }}>
                        #{run.run_number}
                      </td>
                      <td style={tdStyle}>
                        <button
                          onClick={e => { e.stopPropagation(); navigate(`/experiments/${run.experiment_id}`); }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontWeight: 500, fontSize: '0.85rem', padding: 0 }}
                        >
                          {run.experiment_name}
                        </button>
                      </td>
                      <td style={tdStyle}>{run.dataset_name ?? '—'}</td>
                      <td style={tdStyle}>{run.model ? formatModelType(run.model) : '—'}</td>
                      <td style={tdStyle}><StatusBadge status={run.status} /></td>
                      <td style={{ ...tdStyle, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Clock size={12} style={{ opacity: 0.5 }} />
                        {run.started_at ? formatDate(run.started_at) : '—'}
                      </td>
                      <td style={tdStyle}>{run.completed_at ? formatDate(run.completed_at) : '—'}</td>
                      <td style={tdStyle}>{formatDuration(run.duration_seconds)}</td>
                      <td style={tdStyle}>
                        <button
                          onClick={e => { e.stopPropagation(); navigate(`/runs/${run.run_id}`); }}
                          style={{
                            display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                            background: 'var(--accent)18', color: 'var(--accent)',
                            border: '1px solid var(--accent)30', borderRadius: '0.4rem',
                            padding: '0.3rem 0.7rem', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                          }}
                        >
                          View <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
