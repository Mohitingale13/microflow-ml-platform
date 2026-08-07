import { useState } from 'react';
import {
  Activity,
  GitBranch,
  LayoutList,
  Network,
  Workflow,
} from 'lucide-react';
import {
  usePipelineGraph,
  usePipelineLineage,
  usePipelineOverview,
  usePipelineRuns,
} from '@/hooks/usePipeline';
import { PipelineOverviewCards } from '@/components/pipeline/PipelineOverviewCards';
import { PipelineRunsTable } from '@/components/pipeline/PipelineRunsTable';
import { PipelineFlowGraph } from '@/components/pipeline/PipelineFlowGraph';
import { PipelineTimelineComponent } from '@/components/pipeline/PipelineTimeline';
import { DatasetLineage } from '@/components/pipeline/DatasetLineage';

// ─── Tab IDs ──────────────────────────────────────────────────────────────────
type Tab = 'runs' | 'graph' | 'timeline' | 'lineage';

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'runs',     label: 'Executions',    icon: LayoutList  },
  { id: 'graph',    label: 'Flow Graph',    icon: Network     },
  { id: 'timeline', label: 'Timeline',      icon: Activity    },
  { id: 'lineage',  label: 'Lineage',       icon: GitBranch   },
];

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function CardSkeleton({ h = 80 }: { h?: number }) {
  return (
    <div style={{
      height: h, borderRadius: '0.75rem',
      background: 'var(--bg-secondary)',
      animation: 'pulse 1.5s infinite',
    }} />
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────
function EmptyState({ tab }: { tab: Tab }) {
  const msgs: Record<Tab, string> = {
    runs:     'No pipeline runs yet. Execute a Run from the Experiments page to see executions here.',
    graph:    'Select a run from the Executions tab to view its flow graph.',
    timeline: 'Select a run from the Executions tab to view its execution timeline.',
    lineage:  'Upload a dataset and create experiments to see the lineage tree.',
  };
  return (
    <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-muted)' }}>
      <Workflow size={52} style={{ opacity: 0.2, marginBottom: '1rem' }} />
      <p style={{ fontSize: '0.9rem' }}>{msgs[tab]}</p>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export function Pipeline() {
  const [activeTab, setActiveTab] = useState<Tab>('runs');
  const [selectedRunId, setSelectedRunId] = useState<string>('');

  const overviewQuery = usePipelineOverview();
  const runsQuery = usePipelineRuns();
  const graphQuery = usePipelineGraph(selectedRunId);
  const lineageQuery = usePipelineLineage();

  function handleSelectRun(runId: string) {
    setSelectedRunId(runId);
    setActiveTab('graph');
  }

  return (
    <div className="page">
      {/* ── Page Header ── */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Pipeline Visualization</h2>
          <p className="page-subtitle">
            Visual execution graph, timeline, and lineage for every ML workflow
          </p>
        </div>
      </div>

      {/* ── Overview Cards ── */}
      {overviewQuery.isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} h={90} />)}
        </div>
      ) : overviewQuery.data ? (
        <PipelineOverviewCards overview={overviewQuery.data} />
      ) : null}

      {/* ── Tab Navigation ── */}
      <div style={{
        display: 'flex', gap: '0.5rem',
        padding: '0.25rem',
        background: 'var(--color-surface-2)',
        borderRadius: 'var(--radius-md)',
        width: 'fit-content',
        border: '1px solid var(--color-border)',
        marginBottom: '1.5rem',
      }}>
        {TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.45rem',
                padding: '0.5rem 1rem',
                background: isActive ? 'var(--color-surface)' : 'transparent',
                border: 'none',
                borderRadius: 'calc(var(--radius-md) - 2px)',
                color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                fontWeight: isActive ? 700 : 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s',
                boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
              }}
            >
              <Icon size={15} style={{ color: isActive ? 'var(--color-accent-purple)' : 'inherit' }} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ── Tab Content ── */}

      {/* EXECUTIONS TABLE */}
      {activeTab === 'runs' && (
        <>
          {runsQuery.isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} h={52} />)}
            </div>
          ) : runsQuery.data && runsQuery.data.length > 0 ? (
            <PipelineRunsTable
              runs={runsQuery.data}
              onSelectRun={handleSelectRun}
              selectedRunId={selectedRunId}
            />
          ) : (
            <EmptyState tab="runs" />
          )}
        </>
      )}

      {/* FLOW GRAPH + RUNS SIDEBAR */}
      {activeTab === 'graph' && (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* Run selector sidebar */}
          <div className="card" style={{ padding: '0.75rem', maxHeight: 600, overflowY: 'auto' }}>
            <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.25rem 0.5rem 0.5rem' }}>
              Select a Run
            </p>
            {!runsQuery.data || runsQuery.data.length === 0 ? (
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', padding: '0.5rem' }}>No runs available.</p>
            ) : (
              runsQuery.data.map(run => {
                const isSelected = run.run_id === selectedRunId;
                const statusColor: Record<string, string> = {
                  completed: '#22c55e', running: '#3b82f6', failed: '#ef4444',
                  queued: '#f59e0b', draft: '#6b7280',
                };
                const color = statusColor[run.status] ?? '#6b7280';
                return (
                  <button
                    key={run.run_id}
                    onClick={() => setSelectedRunId(run.run_id)}
                    style={{
                      width: '100%', textAlign: 'left',
                      display: 'flex', alignItems: 'center', gap: '0.6rem',
                      padding: '0.6rem 0.75rem',
                      borderRadius: '0.5rem', marginBottom: '0.25rem',
                      background: isSelected ? 'var(--accent)15' : 'transparent',
                      border: isSelected ? '1px solid var(--accent)40' : '1px solid transparent',
                      cursor: 'pointer', transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)'; }}
                    onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                  >
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      #{run.run_number}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {run.experiment_name}
                    </span>
                  </button>
                );
              })
            )}
          </div>

          {/* Graph panel */}
          <div className="card" style={{ minHeight: 500, overflowY: 'auto' }}>
            {!selectedRunId ? (
              <EmptyState tab="graph" />
            ) : graphQuery.isLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem' }}>
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <CardSkeleton h={80} />
                  </div>
                ))}
              </div>
            ) : graphQuery.data?.graph ? (
              <PipelineFlowGraph graph={graphQuery.data.graph} />
            ) : (
              <EmptyState tab="graph" />
            )}
          </div>
        </div>
      )}

      {/* TIMELINE */}
      {activeTab === 'timeline' && (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* Run selector sidebar */}
          <div className="card" style={{ padding: '0.75rem', maxHeight: 600, overflowY: 'auto' }}>
            <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.25rem 0.5rem 0.5rem' }}>
              Select a Run
            </p>
            {!runsQuery.data || runsQuery.data.length === 0 ? (
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', padding: '0.5rem' }}>No runs available.</p>
            ) : (
              runsQuery.data.map(run => {
                const isSelected = run.run_id === selectedRunId;
                const statusColor: Record<string, string> = {
                  completed: '#22c55e', running: '#3b82f6', failed: '#ef4444',
                  queued: '#f59e0b', draft: '#6b7280',
                };
                const color = statusColor[run.status] ?? '#6b7280';
                return (
                  <button
                    key={run.run_id}
                    onClick={() => setSelectedRunId(run.run_id)}
                    style={{
                      width: '100%', textAlign: 'left',
                      display: 'flex', alignItems: 'center', gap: '0.6rem',
                      padding: '0.6rem 0.75rem',
                      borderRadius: '0.5rem', marginBottom: '0.25rem',
                      background: isSelected ? 'var(--accent)15' : 'transparent',
                      border: isSelected ? '1px solid var(--accent)40' : '1px solid transparent',
                      cursor: 'pointer', transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)'; }}
                    onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                  >
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      #{run.run_number}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {run.experiment_name}
                    </span>
                  </button>
                );
              })
            )}
          </div>

          {/* Timeline panel */}
          <div className="card">
            {!selectedRunId ? (
              <EmptyState tab="timeline" />
            ) : graphQuery.isLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '0.5rem' }}>
                {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} h={56} />)}
              </div>
            ) : graphQuery.data?.timeline ? (
              <PipelineTimelineComponent timeline={graphQuery.data.timeline} />
            ) : (
              <EmptyState tab="timeline" />
            )}
          </div>
        </div>
      )}

      {/* LINEAGE */}
      {activeTab === 'lineage' && (
        <>
          {lineageQuery.isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Array.from({ length: 2 }).map((_, i) => <CardSkeleton key={i} h={200} />)}
            </div>
          ) : lineageQuery.data && lineageQuery.data.length > 0 ? (
            <DatasetLineage datasets={lineageQuery.data} />
          ) : (
            <EmptyState tab="lineage" />
          )}
        </>
      )}
    </div>
  );
}
