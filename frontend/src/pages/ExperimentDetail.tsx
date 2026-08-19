import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, FlaskConical, Play, Settings2, Tag, Info,
  LayoutGrid, Plus, Archive, Trash2, AlertCircle, Sparkles,
} from 'lucide-react';
import { useExperiment, useExperimentRuns, useUpdateExperiment, useDeleteExperiment } from '../hooks/useExperiments';
import { useDataset } from '../hooks/useDatasets';
import { RunTable } from '../components/experiments/RunTable';
import { ConfigurationViewer } from '../components/experiments/ConfigurationViewer';
import { ExperimentStatusBadge, RunStatusBadge } from '../components/experiments/RunStatusBadge';
import { CreateRunModal } from '../components/experiments/CreateRunModal';
import { InvestigatorModal } from '../components/experiments/InvestigatorModal';
import { CompareRunsDialog } from '../components/experiments/CompareRunsDialog';
import { ConfirmationDialog } from '../components/common/ConfirmationDialog';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { AIStrategyTab } from '../components/experiments/AIStrategyTab';

type Tab = 'overview' | 'runs' | 'configuration' | 'metadata' | 'ai-strategy';

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [isCreateRunOpen, setIsCreateRunOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
    const [isInvestigatorOpen, setIsInvestigatorOpen] = useState(false);
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: experiment, isLoading, error } = useExperiment(id!);
  const { data: runs = [], isLoading: isLoadingRuns } = useExperimentRuns(id!);
  const { data: dataset } = useDataset(experiment?.dataset_id ?? '');

  const updateMutation = useUpdateExperiment(id!);
  const deleteMutation = useDeleteExperiment();

  const handleActivate = async () => {
    setActionError(null);
    try {
      await updateMutation.mutateAsync({ status: 'active' });
    } catch (err: any) {
      setActionError(err?.response?.data?.message || err?.message || 'Failed to activate experiment');
    }
  };

  const handleArchive = async () => {
    setActionError(null);
    try {
      await updateMutation.mutateAsync({ status: 'archived' });
      setShowArchiveConfirm(false);
    } catch (err: any) {
      setActionError(err?.response?.data?.message || err?.message || 'Failed to archive experiment');
    }
  };

  const handleDelete = async () => {
    setActionError(null);
    try {
      if (experiment?.status === 'active') {
        // Active experiments must be archived first per delete guards
        await updateMutation.mutateAsync({ status: 'archived' });
      }
      await deleteMutation.mutateAsync(id!);
      navigate('/experiments');
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || 'Failed to delete experiment';
      setActionError(msg);
    }
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode; count?: number }[] = [
    { id: 'overview',       label: 'Overview',       icon: <LayoutGrid className="w-4 h-4" /> },
    { id: 'runs',           label: 'Runs',           icon: <Play className="w-4 h-4" />, count: runs.length },
    { id: 'configuration',  label: 'Configuration',  icon: <Settings2 className="w-4 h-4" /> },
    { id: 'metadata',       label: 'Metadata',       icon: <Info className="w-4 h-4" /> },
    { id: 'ai-strategy',    label: 'AI Strategy',    icon: <Sparkles className="w-4 h-4 text-indigo-400" /> },
  ];

  if (isLoading) {
    return (
      <div className="page">
        <div className="h-8 w-40 bg-surface-2 rounded animate-pulse mb-6" />
        <TableSkeleton rows={4} cols={4} />
      </div>
    );
  }

  if (error || !experiment) {
    return (
      <div className="page">
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Failed to load experiment</h3>
            <p className="text-sm opacity-90">{(error as Error)?.message || 'Not found'}</p>
          </div>
        </div>
        <button onClick={() => navigate('/experiments')} className="mt-4 btn btn--secondary inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Experiments
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      {/* Back */}
      <button
        onClick={() => navigate('/experiments')}
        className="text-text-muted hover:text-text-primary flex items-center gap-1.5 text-sm font-medium mb-5 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Experiments
      </button>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-5 mb-6">
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-11 h-11 rounded-lg bg-accent-blue/10 flex items-center justify-center shrink-0">
            <FlaskConical className="w-5 h-5 text-accent-blue" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center flex-wrap gap-2 mb-1">
              <h1 className="text-xl font-bold text-text-primary tracking-tight truncate">{experiment.name}</h1>
              <ExperimentStatusBadge status={experiment.status} />
            </div>
            {experiment.description && (
              <p className="text-sm text-text-muted leading-relaxed max-w-2xl">{experiment.description}</p>
            )}
            {experiment.objective && (
              <p className="text-xs text-text-muted/70 italic mt-1">Objective: {experiment.objective}</p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0 w-full lg:w-auto mt-2 lg:mt-0">
          {/* Compare Runs button — always visible, disabled when fewer than 2 completed runs */}
          {(() => {
            const completedCount = runs.filter((r) => r.status === 'completed').length;
            const disabled = completedCount < 2;
            return (
              <div
                title={disabled ? 'At least two completed runs are required to generate an AI comparison.' : 'Compare two completed runs with AI'}
              >
                <button
                  id="compare-runs-btn"
                  onClick={() => setIsCompareOpen(true)}
                  disabled={disabled}
                  className="px-3 py-2 text-sm font-medium text-accent-blue border border-accent-blue/20 bg-accent-blue/5 rounded hover:bg-accent-blue/10 flex items-center gap-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Compare Runs
                </button>
              </div>
            );
          })()}
            <button
              onClick={() => setIsInvestigatorOpen(true)}
              className="px-3 py-2 text-sm font-medium text-purple-600 border border-purple-200 bg-purple-50 rounded hover:bg-purple-100 flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5" /> AI Investigator
            </button>
          {experiment.status === 'draft' && (
            <button
              onClick={handleActivate}
              disabled={updateMutation.isPending}
              className="px-3 py-2 text-sm font-medium text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 rounded hover:bg-emerald-500/20 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" /> Activate
            </button>
          )}
          {experiment.status !== 'archived' && (
            <button
              onClick={() => setShowArchiveConfirm(true)}
              className="px-3 py-2 text-sm font-medium text-text-muted border border-border rounded hover:bg-surface-2 flex items-center gap-1.5 transition-colors"
            >
              <Archive className="w-3.5 h-3.5" /> Archive
            </button>
          )}
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-3 py-2 text-sm font-medium text-red-400 border border-red-500/20 bg-red-500/5 rounded hover:bg-red-500/10 flex items-center gap-1.5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" /> Delete
          </button>
        </div>
      </div>

      {actionError && (
        <div className="p-4 mb-6 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Tactile, Mobile-First Interactive Tab Buttons */}
      <div className="mb-8">
        <div className="flex items-center gap-2 p-2 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-2xl w-full overflow-x-auto scrollbar-hide">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const isAI = tab.id === 'ai-strategy';
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`shrink-0 flex items-center justify-center gap-2.5 py-2.5 px-5 rounded-xl text-sm font-bold transition-all duration-200 whitespace-nowrap select-none cursor-pointer ${
                  isActive
                    ? isAI
                      ? 'bg-gradient-to-r from-indigo-500 via-purple-600 to-indigo-600 text-white shadow-md border border-indigo-300/40'
                      : 'bg-[var(--color-surface)] text-[var(--color-text-primary)] border border-[var(--color-border)] shadow-sm'
                    : 'bg-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] border border-transparent'
                }`}
              >
                <span className={isActive && isAI ? 'text-indigo-200 animate-pulse' : 'text-inherit opacity-80'}>
                  {tab.icon}
                </span>
                <span className="tracking-wide">{tab.label}</span>
                {tab.count !== undefined && (
                  <span className={`text-xs rounded-full px-2.5 py-0.5 min-w-[24px] text-center font-mono font-extrabold ${
                    isActive ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] border border-[var(--color-border)]' : 'bg-[var(--color-surface-2)] text-[var(--color-text-secondary)] border border-transparent'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <InfoCard label="Experiment Status" value={<ExperimentStatusBadge status={experiment.status} />} />
            <InfoCard label="Dataset" value={dataset?.name ?? experiment.dataset_id} />
            <InfoCard label="Total Runs" value={String(runs.length)} />
            <InfoCard label="Created" value={formatDate(experiment.created_at)} />
          </div>

          {runs.length > 0 && (
            <div className="bg-surface border border-border rounded-lg p-5">
              <h3 className="text-xs text-text-muted uppercase tracking-wider font-semibold mb-3">
                Runs Status Breakdown
              </h3>
              <div className="flex flex-wrap gap-3">
                {(['draft', 'queued', 'running', 'completed', 'failed', 'cancelled'] as const).map((st) => {
                  const count = runs.filter((r) => r.status === st).length;
                  if (count === 0) return null;
                  return (
                    <div key={st} className="flex items-center gap-2 bg-surface-2 border border-border px-3 py-1.5 rounded-md text-xs">
                      <RunStatusBadge status={st} />
                      <span className="font-semibold text-text-primary">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {experiment.tags && experiment.tags.length > 0 && (
            <div className="bg-surface border border-border rounded-lg p-5">
              <p className="text-xs text-text-muted uppercase tracking-wider font-medium mb-3 flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5" /> Tags
              </p>
              <div className="flex flex-wrap gap-2">
                {experiment.tags.map((tag) => (
                  <span key={tag} className="text-xs font-medium bg-accent-blue/10 text-accent-blue border border-accent-blue/20 rounded-full px-2.5 py-1">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'runs' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-text-primary">
              {runs.length} run{runs.length !== 1 ? 's' : ''}
            </h3>
            <button
              id="create-run-btn"
              onClick={() => setIsCreateRunOpen(true)}
              className="btn btn--primary flex items-center gap-2 text-sm py-1.5"
            >
              <Plus className="w-4 h-4" /> New Run
            </button>
          </div>
          {isLoadingRuns ? (
            <TableSkeleton rows={3} cols={5} />
          ) : (
            <RunTable runs={runs} experimentId={id!} />
          )}
        </div>
      )}

      {activeTab === 'configuration' && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-4">Default Configuration</h3>
          <ConfigurationViewer config={experiment.default_configuration} />
        </div>
      )}

      {activeTab === 'metadata' && (
        <div className="bg-surface border border-border rounded-lg p-6 space-y-5">
          <MetaRow label="Experiment ID" value={experiment.id} mono />
          <MetaRow label="Dataset ID" value={experiment.dataset_id} mono />
          <MetaRow label="Created At" value={formatDate(experiment.created_at)} />
          <MetaRow label="Updated At" value={formatDate(experiment.updated_at)} />
          <MetaRow label="Status" value={experiment.status} />
        </div>
      )}

      {activeTab === 'ai-strategy' && (
        <AIStrategyTab experimentId={id!} />
      )}

      {/* Compare Runs Dialog */}
      <CompareRunsDialog
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        experimentId={id!}
        runs={runs}
      />

      <InvestigatorModal
        isOpen={isInvestigatorOpen}
        onClose={() => setIsInvestigatorOpen(false)}
        experimentId={id!}
      />

      {/* Create Run Modal */}
      <CreateRunModal
        isOpen={isCreateRunOpen}
        onClose={() => setIsCreateRunOpen(false)}
        experimentId={id!}
        experimentDefaultConfig={experiment.default_configuration}
      />

      <ConfirmationDialog
        isOpen={showArchiveConfirm}
        title="Archive Experiment"
        description="Archiving will prevent new runs from being created. You can still view existing data."
        confirmLabel="Archive"
        onConfirm={handleArchive}
        onCancel={() => setShowArchiveConfirm(false)}
        isLoading={updateMutation.isPending}
        variant="warning"
      />

      <ConfirmationDialog
        isOpen={showDeleteConfirm}
        title="Delete Experiment"
        description={
          experiment.status === 'active'
            ? 'This experiment is currently Active. In accordance with delete safety guards, active experiments must be archived before deletion. Proceeding will archive and permanently delete this experiment and all its runs.'
            : 'This will permanently delete the experiment and all its runs. This action cannot be undone.'
        }
        confirmLabel={experiment.status === 'active' ? 'Archive & Delete' : 'Delete'}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
        isLoading={deleteMutation.isPending || updateMutation.isPending}
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

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <span className="block text-xs text-text-muted mb-1 font-medium uppercase tracking-wider">{label}</span>
      <code className={`text-sm text-text-primary ${mono ? 'font-mono bg-surface-2 px-2 py-1 rounded break-all' : ''}`}>
        {value}
      </code>
    </div>
  );
}
