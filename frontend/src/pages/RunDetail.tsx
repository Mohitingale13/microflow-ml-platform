import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Terminal,
  Settings2,
  Info,
  LayoutGrid,
  PlayCircle,
  XCircle,
  Trash2,
  AlertCircle,
  Clock,
  Play,
  BarChart2,
  Package,
  Download,
  Eye,
  FileCode,
  CheckCircle2,
  Timer,
} from 'lucide-react';
import {
  useRun,
  useQueueRun,
  useCancelRun,
  useDeleteRun,
  useExecuteRun,
  useRunResult,
  useRunArtifacts,
  useExperiment,
} from '../hooks/useExperiments';
import { useDataset } from '../hooks/useDatasets';
import { ConfigurationViewer } from '../components/experiments/ConfigurationViewer';
import { RunStatusBadge } from '../components/experiments/RunStatusBadge';
import { ConfirmationDialog } from '../components/common/ConfirmationDialog';
import { ExecuteRunModal } from '../components/experiments/ExecuteRunModal';
import { TableSkeleton, CardSkeleton } from '../components/common/LoadingSkeleton';
import { ArtifactTypeBadge } from '../components/artifacts/ArtifactTypeBadge';
import { ArtifactDetailModal } from '../components/artifacts/ArtifactDetailModal';
import { formatBytes, formatModelType } from '../utils/format';
import { getArtifactDownloadUrl } from '../services/artifact.service';
import type { EvaluationMetrics } from '../types/experiment.types';
import type { Artifact } from '../types/artifact.types';

type Tab = 'overview' | 'results' | 'artifacts' | 'configuration' | 'timeline' | 'metadata';

const QUEUEABLE = ['draft'];
const CANCELLABLE = ['draft', 'queued'];

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [confirmAction, setConfirmAction] = useState<'queue' | 'cancel' | 'delete' | null>(null);
  const [isExecuteOpen, setIsExecuteOpen] = useState(false);
  const [executionMetrics, setExecutionMetrics] = useState<EvaluationMetrics | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);

  const { data: run, isLoading, error } = useRun(id!);
  const { data: experiment } = useExperiment(run?.experiment_id ?? '');
  const { data: dataset } = useDataset(experiment?.dataset_id ?? '');

  // Persistent Run Result & Artifacts
  const { data: runResult, isLoading: isLoadingResult } = useRunResult(id!);
  const { data: artifacts = [], isLoading: isLoadingArtifacts } = useRunArtifacts(id!);

  const queueMutation = useQueueRun();
  const cancelMutation = useCancelRun();
  const deleteMutation = useDeleteRun();
  const executeMutation = useExecuteRun();

  // Effective metrics: prefer DB persisted result, fallback to in-memory mutation result
  const effectiveMetrics = useMemo(() => {
    if (runResult) {
      return {
        accuracy: runResult.accuracy,
        precision: runResult.precision,
        recall: runResult.recall,
        f1_score: runResult.f1_score,
        roc_auc: runResult.roc_auc,
        confusion_matrix: runResult.confusion_matrix,
      };
    }
    return executionMetrics;
  }, [runResult, executionMetrics]);

  const handleConfirmAction = async () => {
    if (!run) return;
    try {
      if (confirmAction === 'queue') {
        await queueMutation.mutateAsync({ id: run.id, experimentId: run.experiment_id });
      } else if (confirmAction === 'cancel') {
        await cancelMutation.mutateAsync({ id: run.id, experimentId: run.experiment_id });
      } else if (confirmAction === 'delete') {
        await deleteMutation.mutateAsync(run.id);
        navigate(`/experiments/${run.experiment_id}`);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setConfirmAction(null);
    }
  };

  const handleExecute = async (payload: { target_column: string; test_split?: number }) => {
    if (!run) return;
    setExecutionError(null);
    try {
      if (run.status === 'draft') {
        await queueMutation.mutateAsync({ id: run.id, experimentId: run.experiment_id });
      }
      const res = await executeMutation.mutateAsync({
        id: run.id,
        experimentId: run.experiment_id,
        payload,
      });
      if (res.data?.metrics) {
        setExecutionMetrics(res.data.metrics);
      }
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || 'Execution failed';
      setExecutionError(msg);
      throw err;
    }
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode; badge?: string | number }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutGrid className="w-4 h-4" /> },
    {
      id: 'results',
      label: 'Evaluation Results',
      icon: <BarChart2 className="w-4 h-4" />,
      badge: effectiveMetrics ? 'Ready' : undefined,
    },
    {
      id: 'artifacts',
      label: 'Artifacts',
      icon: <Package className="w-4 h-4" />,
      badge: artifacts.length > 0 ? artifacts.length : undefined,
    },
    { id: 'configuration', label: 'Configuration', icon: <Settings2 className="w-4 h-4" /> },
    { id: 'timeline', label: 'Timeline', icon: <Clock className="w-4 h-4" /> },
    { id: 'metadata', label: 'Metadata', icon: <Info className="w-4 h-4" /> },
  ];

  if (isLoading) {
    return (
      <div className="page">
        <div className="h-8 w-40 bg-surface-2 rounded animate-pulse mb-6" />
        <TableSkeleton rows={4} cols={4} />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="page">
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Failed to load run</h3>
            <p className="text-sm opacity-90">{(error as Error)?.message || 'Not found'}</p>
          </div>
        </div>
        <button
          onClick={() => navigate('/experiments')}
          className="mt-4 btn btn--secondary inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Experiments
        </button>
      </div>
    );
  }

  const isActing =
    queueMutation.isPending ||
    cancelMutation.isPending ||
    deleteMutation.isPending ||
    executeMutation.isPending;

  return (
    <div className="page">
      {/* Back */}
      <button
        onClick={() => navigate(`/experiments/${run.experiment_id}`)}
        className="text-text-muted hover:text-text-primary flex items-center gap-1.5 text-sm font-medium mb-5 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Experiment
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-6 mb-6">
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-11 h-11 rounded-lg bg-surface-2 flex items-center justify-center shrink-0 border border-border">
            <Terminal className="w-5 h-5 text-text-muted" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center flex-wrap gap-3 mb-1">
              <h1 className="text-xl font-bold font-mono text-text-primary tracking-tight truncate">
                Run #{run.run_number}
              </h1>
              <RunStatusBadge status={run.status} />
            </div>
            {run.notes && (
              <p className="text-sm text-text-muted leading-relaxed max-w-2xl">{run.notes}</p>
            )}
            {experiment && (
              <p className="text-xs text-text-muted/70 mt-1">Experiment: {experiment.name}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Execute Button */}
          {(run.status === 'queued' || run.status === 'draft') && (
            <button
              onClick={() => setIsExecuteOpen(true)}
              disabled={isActing}
              className="btn btn--primary flex items-center gap-1.5 text-sm font-medium px-4 py-2"
            >
              <Play className="w-4 h-4" /> Execute Run
            </button>
          )}

          {QUEUEABLE.includes(run.status) && (
            <button
              onClick={() => setConfirmAction('queue')}
              disabled={isActing}
              className="px-3 py-2 text-sm font-medium text-text-primary border border-border rounded bg-surface hover:bg-surface-2 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <PlayCircle className="w-3.5 h-3.5" /> Queue
            </button>
          )}
          {CANCELLABLE.includes(run.status) && (
            <button
              onClick={() => setConfirmAction('cancel')}
              disabled={isActing}
              className="px-3 py-2 text-sm font-medium text-amber-400 border border-amber-500/20 rounded bg-amber-500/5 hover:bg-amber-500/10 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" /> Cancel
            </button>
          )}
          <button
            onClick={() => setConfirmAction('delete')}
            disabled={isActing}
            className="px-3 py-2 text-sm font-medium text-red-400 border border-red-500/20 bg-red-500/5 rounded hover:bg-red-500/10 flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" /> Delete
          </button>
        </div>
      </div>

      {executionError && (
        <div className="p-4 mb-6 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>Execution failed: {executionError}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-border mb-6">
        <div className="flex gap-0 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-4 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-accent-blue text-accent-blue'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold ${
                    activeTab === tab.id
                      ? 'bg-accent-blue/20 text-accent-blue'
                      : 'bg-surface-2 text-text-muted'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <InfoCard label="Status" value={<RunStatusBadge status={run.status} />} />
            <InfoCard label="Model Type" value={formatModelType(run.model_type)} />
            <InfoCard label="Created At" value={formatDate(run.created_at)} />
            <InfoCard label="Updated At" value={formatDate(run.updated_at)} />
          </div>

          {/* Quick Metrics preview on Overview if available */}
          {effectiveMetrics ? (
            <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-accent-cyan" />
                  <h3 className="text-base font-semibold text-text-primary">Evaluation Summary</h3>
                </div>
                <button
                  onClick={() => setActiveTab('results')}
                  className="text-xs text-accent-blue hover:underline font-medium"
                >
                  View full results & matrix →
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <MetricCard
                  label="Accuracy"
                  value={(effectiveMetrics.accuracy * 100).toFixed(1) + '%'}
                  color="text-accent-cyan"
                />
                <MetricCard
                  label="Precision"
                  value={(effectiveMetrics.precision * 100).toFixed(1) + '%'}
                  color="text-accent-blue"
                />
                <MetricCard
                  label="Recall"
                  value={(effectiveMetrics.recall * 100).toFixed(1) + '%'}
                  color="text-accent-purple"
                />
                <MetricCard
                  label="F1 Score"
                  value={(effectiveMetrics.f1_score * 100).toFixed(1) + '%'}
                  color="text-accent-emerald"
                />
              </div>
            </div>
          ) : run.status === 'completed' && isLoadingResult ? (
            <div className="mt-4">
              <CardSkeleton count={4} />
            </div>
          ) : null}

          {/* Artifacts snapshot if completed */}
          {artifacts.length > 0 && (
            <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-accent-blue" />
                  <h3 className="text-base font-semibold text-text-primary">
                    Produced Artifacts ({artifacts.length})
                  </h3>
                </div>
                <button
                  onClick={() => setActiveTab('artifacts')}
                  className="text-xs text-accent-blue hover:underline font-medium"
                >
                  View all artifacts →
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {artifacts.map((art) => (
                  <div
                    key={art.id}
                    className="p-3 bg-surface-2 border border-border rounded-lg flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-mono font-medium text-text-primary truncate">
                        {art.filename}
                      </p>
                      <p className="text-[11px] text-text-muted mt-0.5">
                        {formatBytes(art.file_size_bytes)}
                      </p>
                    </div>
                    <a
                      href={getArtifactDownloadUrl(art.id)}
                      download={art.filename}
                      className="p-1.5 rounded text-text-muted hover:text-accent-blue hover:bg-surface transition-colors shrink-0"
                      title="Download"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && (
        <div className="space-y-6">
          {effectiveMetrics ? (
            <div className="space-y-6">
              {/* Timing info if available */}
              {runResult?.completed_at && (
                <div className="p-4 bg-surface border border-border rounded-xl flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
                    <span>
                      Evaluated on{' '}
                      <strong className="text-text-primary">
                        {new Date(runResult.completed_at).toLocaleString()}
                      </strong>
                    </span>
                  </div>
                  {runResult.execution_time_seconds !== null &&
                    runResult.execution_time_seconds !== undefined && (
                      <div className="flex items-center gap-1.5 text-xs text-text-muted">
                        <Timer className="w-3.5 h-3.5" />
                        <span>Execution time:</span>
                        <strong className="text-text-primary font-mono">
                          {runResult.execution_time_seconds.toFixed(2)}s
                        </strong>
                      </div>
                    )}
                </div>
              )}

              {/* Metric Cards */}
              <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart2 className="w-5 h-5 text-accent-cyan" />
                  <h3 className="text-base font-semibold text-text-primary">Classification Metrics</h3>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                  <MetricCard
                    label="Accuracy"
                    value={(effectiveMetrics.accuracy * 100).toFixed(1) + '%'}
                    color="text-accent-cyan"
                  />
                  <MetricCard
                    label="Precision"
                    value={(effectiveMetrics.precision * 100).toFixed(1) + '%'}
                    color="text-accent-blue"
                  />
                  <MetricCard
                    label="Recall"
                    value={(effectiveMetrics.recall * 100).toFixed(1) + '%'}
                    color="text-accent-purple"
                  />
                  <MetricCard
                    label="F1 Score"
                    value={(effectiveMetrics.f1_score * 100).toFixed(1) + '%'}
                    color="text-accent-emerald"
                  />
                </div>

                {effectiveMetrics.roc_auc !== undefined && effectiveMetrics.roc_auc !== null && (
                  <div className="mb-6 p-4 bg-surface-2 rounded-lg border border-border flex justify-between items-center">
                    <span className="text-sm font-medium text-text-secondary">ROC AUC Score</span>
                    <span className="text-lg font-mono font-bold text-accent-cyan">
                      {(effectiveMetrics.roc_auc * 100).toFixed(1)}%
                    </span>
                  </div>
                )}

                {effectiveMetrics.confusion_matrix && (
                  <div>
                    <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                      Confusion Matrix
                    </h4>
                    <div className="inline-block bg-surface-2 p-3 rounded-lg border border-border font-mono text-xs text-text-primary">
                      <table className="border-collapse">
                        <tbody>
                          {effectiveMetrics.confusion_matrix.map((row, rIdx) => (
                            <tr key={rIdx}>
                              {row.map((val, cIdx) => (
                                <td
                                  key={cIdx}
                                  className="px-4 py-2.5 text-center border border-border font-bold text-sm"
                                >
                                  {val}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 bg-surface border border-border rounded-xl text-center">
              <BarChart2 className="w-10 h-10 text-text-muted mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                No Evaluation Results Available
              </h3>
              <p className="text-xs text-text-muted max-w-sm mx-auto">
                Execute this run to train the model and generate persistent evaluation results.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Artifacts Tab */}
      {activeTab === 'artifacts' && (
        <div className="space-y-4">
          {isLoadingArtifacts ? (
            <TableSkeleton rows={4} cols={5} />
          ) : artifacts.length === 0 ? (
            <div className="p-12 bg-surface border border-border rounded-xl text-center">
              <Package className="w-10 h-10 text-text-muted mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                No Artifacts Produced Yet
              </h3>
              <p className="text-xs text-text-muted max-w-sm mx-auto">
                Artifacts such as models, metrics JSON, and summaries will appear here once training completes.
              </p>
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-border text-xs font-semibold uppercase tracking-wider text-text-muted">
                    <th className="px-4 py-3.5">Filename</th>
                    <th className="px-4 py-3.5">Type</th>
                    <th className="px-4 py-3.5">Size</th>
                    <th className="px-4 py-3.5">Created</th>
                    <th className="px-4 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {artifacts.map((art) => (
                    <tr key={art.id} className="hover:bg-surface-2/60 transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-text-muted shrink-0" />
                          <span className="font-mono text-xs font-medium text-text-primary">
                            {art.filename}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <ArtifactTypeBadge type={art.artifact_type} size="sm" />
                      </td>
                      <td className="px-4 py-3.5 text-xs font-mono text-text-secondary">
                        {formatBytes(art.file_size_bytes)}
                      </td>
                      <td className="px-4 py-3.5 text-xs text-text-muted">
                        {new Date(art.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setSelectedArtifact(art)}
                            title="View Metadata"
                            className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <a
                            href={getArtifactDownloadUrl(art.id)}
                            download={art.filename}
                            title="Download Artifact"
                            className="p-1.5 rounded text-text-muted hover:text-accent-blue hover:bg-accent-blue/10 transition-colors inline-flex items-center"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'configuration' && (
        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-1">Resolved Configuration</h3>
            <p className="text-xs text-text-muted mb-4">
              The final configuration applied to this run (experiment defaults + run overrides).
            </p>
            <ConfigurationViewer config={run.training_configuration} />
          </div>
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="relative pl-6 border-l-2 border-border space-y-8">
            <TimelineItem
              title="Run Created"
              time={formatDate(run.created_at)}
              description="Run was initialized in draft state."
              active={true}
            />
            {['queued', 'running', 'completed', 'failed', 'cancelled'].includes(run.status) && (
              <TimelineItem
                title="Status Updated"
                time={formatDate(run.updated_at)}
                description={`Run transitioned to ${run.status}.`}
                active={true}
              />
            )}
            {run.status === 'completed' && (
              <TimelineItem
                title="Execution Finished"
                time={formatDate(run.updated_at)}
                description="Run completed successfully and persistent artifacts were generated."
                active={true}
              />
            )}
          </div>
        </div>
      )}

      {activeTab === 'metadata' && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-5">
          <MetaRow label="Run ID" value={run.id} mono />
          <MetaRow label="Experiment ID" value={run.experiment_id} mono />
          <MetaRow label="Run Number" value={String(run.run_number)} />
          <MetaRow label="Created At" value={formatDate(run.created_at)} />
          <MetaRow label="Updated At" value={formatDate(run.updated_at)} />
        </div>
      )}

      {/* Artifact Metadata Modal */}
      {selectedArtifact && (
        <ArtifactDetailModal
          isOpen
          onClose={() => setSelectedArtifact(null)}
          artifact={selectedArtifact}
          experiment={experiment ? { ...experiment, run_count: 0 } as any : undefined}
          dataset={dataset ? { ...dataset, column_count: 0, row_count: 0, file_size_bytes: 0 } as any : undefined}
        />
      )}

      {/* Dialogs */}
      <ExecuteRunModal
        isOpen={isExecuteOpen}
        onClose={() => setIsExecuteOpen(false)}
        onExecute={handleExecute}
        isLoading={executeMutation.isPending}
        dataset={dataset}
        defaultSplit={
          typeof run.training_configuration?.test_split === 'number'
            ? run.training_configuration.test_split
            : 0.2
        }
      />
      <ConfirmationDialog
        isOpen={confirmAction === 'queue'}
        title={`Queue Run #${run.run_number}`}
        description="This will move the run to the queued state, ready for execution."
        confirmLabel="Queue Run"
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
        isLoading={isActing}
        variant="warning"
      />
      <ConfirmationDialog
        isOpen={confirmAction === 'cancel'}
        title={`Cancel Run #${run.run_number}`}
        description="This will cancel the run. This action cannot be undone."
        confirmLabel="Cancel Run"
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
        isLoading={isActing}
        variant="danger"
      />
      <ConfirmationDialog
        isOpen={confirmAction === 'delete'}
        title={`Delete Run #${run.run_number}`}
        description="This will permanently delete the run. This action cannot be undone."
        confirmLabel="Delete Run"
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
        isLoading={isActing}
        variant="danger"
      />
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <p className="text-xs text-text-muted uppercase tracking-wider font-medium mb-2">{label}</p>
      <div className="text-sm font-semibold text-text-primary">{value}</div>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-surface-2 border border-border rounded-lg p-4">
      <p className="text-xs text-text-muted uppercase tracking-wider font-medium mb-1">{label}</p>
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <span className="block text-xs text-text-muted mb-1 font-medium uppercase tracking-wider">
        {label}
      </span>
      <code
        className={`text-sm text-text-primary ${
          mono ? 'font-mono bg-surface-2 px-2 py-1 rounded break-all' : ''
        }`}
      >
        {value}
      </code>
    </div>
  );
}

function TimelineItem({
  title,
  time,
  description,
  active,
}: {
  title: string;
  time: string;
  description: string;
  active: boolean;
}) {
  return (
    <div className="relative">
      <div
        className={`absolute -left-[31px] w-4 h-4 rounded-full border-2 ${
          active ? 'bg-accent-blue border-surface' : 'bg-surface border-border'
        }`}
      />
      <h4 className={`text-sm font-semibold ${active ? 'text-text-primary' : 'text-text-muted'}`}>
        {title}
      </h4>
      <span className="text-xs text-text-muted block mb-1">{time}</span>
      <p className="text-sm text-text-secondary">{description}</p>
    </div>
  );
}
