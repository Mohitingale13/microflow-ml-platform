import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  Brain,
  FlaskConical,
  X,
  CheckCircle2,
} from 'lucide-react';
import { useRuns, useExperiments, useQueueRun, useCancelRun, useExecuteRun } from '@/hooks/useExperiments';
import { useDatasets, useDataset } from '@/hooks/useDatasets';
import { TrainingStats } from '@/components/training/TrainingStats';
import { GlobalRunTable } from '@/components/training/GlobalRunTable';
import { ExecuteRunModal } from '@/components/experiments/ExecuteRunModal';
import { CardSkeleton, TableSkeleton } from '@/components/common/LoadingSkeleton';
import { SUPPORTED_MODELS } from '@/utils/format';
import type { RunListItem } from '@/types/experiment.types';

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'queued', label: 'Queued' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export function Training() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [selectedRunForExecute, setSelectedRunForExecute] = useState<RunListItem | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [refreshSuccess, setRefreshSuccess] = useState(false);

  async function handleRefresh() {
    setIsManualRefreshing(true);
    const start = Date.now();
    try {
      await refetchRuns();
      const elapsed = Date.now() - start;
      if (elapsed < 500) await new Promise(r => setTimeout(r, 500 - elapsed));
    } finally {
      setIsManualRefreshing(false);
      setRefreshSuccess(true);
      setTimeout(() => setRefreshSuccess(false), 2000);
    }
  }

  // Queries
  const {
    data: runs = [],
    isLoading: isLoadingRuns,
    error: runsError,
    refetch: refetchRuns,
    isRefetching: isRefetchingRuns,
  } = useRuns();

  const {
    data: experiments = [],
    isLoading: isLoadingExperiments,
  } = useExperiments();

  const {
    data: datasets = [],
    isLoading: isLoadingDatasets,
  } = useDatasets();

  // Mutations
  const queueMutation = useQueueRun();
  const cancelMutation = useCancelRun();
  const executeMutation = useExecuteRun();

  // Quick lookup maps
  const experimentsMap = useMemo(
    () => new Map(experiments.map((e) => [e.id, e])),
    [experiments]
  );

  const datasetsMap = useMemo(
    () => new Map(datasets.map((d) => [d.id, d])),
    [datasets]
  );

  // Filtered runs
  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      // Status filter
      if (statusFilter !== 'all' && run.status !== statusFilter) {
        return false;
      }

      // Model filter
      if (modelFilter !== 'all') {
        const runModel = run.model_type?.toLowerCase() || 'random_forest';
        if (runModel !== modelFilter.toLowerCase()) {
          return false;
        }
      }

      // Search term
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase().trim();
        const runNumStr = `#${run.run_number}`.toLowerCase();
        const experiment = experimentsMap.get(run.experiment_id);
        const expName = experiment?.name.toLowerCase() || '';
        const dataset = experiment ? datasetsMap.get(experiment.dataset_id) : undefined;
        const datasetName = dataset?.name.toLowerCase() || '';
        const modelName = run.model_type?.toLowerCase() || '';

        const matches =
          runNumStr.includes(term) ||
          run.id.toLowerCase().includes(term) ||
          expName.includes(term) ||
          datasetName.includes(term) ||
          modelName.includes(term) ||
          run.status.toLowerCase().includes(term);

        if (!matches) return false;
      }

      return true;
    });
  }, [runs, statusFilter, modelFilter, searchTerm, experimentsMap, datasetsMap]);

  // Actions
  const handleQueueRun = async (runId: string, experimentId: string) => {
    setActionError(null);
    try {
      await queueMutation.mutateAsync({ id: runId, experimentId });
    } catch (err: any) {
      setActionError(err?.message || 'Failed to queue run.');
    }
  };

  const handleCancelRun = async (runId: string, experimentId: string) => {
    setActionError(null);
    try {
      await cancelMutation.mutateAsync({ id: runId, experimentId });
    } catch (err: any) {
      setActionError(err?.message || 'Failed to cancel run.');
    }
  };

  const handleExecuteSubmit = async (payload: {
    target_column: string;
    test_split?: number;
  }) => {
    if (!selectedRunForExecute) return;
    setActionError(null);
    try {
      await executeMutation.mutateAsync({
        id: selectedRunForExecute.id,
        experimentId: selectedRunForExecute.experiment_id,
        payload,
      });
      setSelectedRunForExecute(null);
    } catch (err: any) {
      const msg = err?.message || 'Execution failed';
      setActionError(msg);
      throw err;
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setModelFilter('all');
  };

  const hasActiveFilters =
    searchTerm.trim() !== '' || statusFilter !== 'all' || modelFilter !== 'all';

  const isInitialLoading =
    isLoadingRuns || isLoadingExperiments || isLoadingDatasets;

  // Selected experiment & dataset for the execution modal
  const selectedExperiment = selectedRunForExecute
    ? experimentsMap.get(selectedRunForExecute.experiment_id)
    : null;
  const { data: fullDataset } = useDataset(selectedExperiment?.dataset_id ?? '');

  return (
    <div className="page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Training Operations
          </h1>
          <p className="text-sm text-text-muted mt-0.5">
            Execute and monitor model training workloads across all experiments
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRefresh}
            disabled={isRefetchingRuns || isManualRefreshing}
            className="px-3.5 py-2 text-xs font-bold text-gray-200 hover:text-white border border-white/15 rounded-xl bg-white/5 hover:bg-white/10 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer disabled:opacity-50"
            title="Refresh runs"
          >
            {refreshSuccess ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300">Updated!</span>
              </>
            ) : (
              <>
                <RefreshCw
                  className={`w-3.5 h-3.5 ${isRefetchingRuns || isManualRefreshing ? 'animate-spin text-purple-300' : ''}`}
                />
                <span>{isRefetchingRuns || isManualRefreshing ? 'Refreshing...' : 'Refresh'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Action Error Banner */}
      {actionError && (
        <div className="p-4 mb-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{actionError}</span>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-red-400/70 hover:text-red-400"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error state */}
      {runsError && (
        <div className="p-4 mb-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold mb-0.5">Failed to load training runs</h4>
            <p className="text-xs opacity-90">
              {(runsError as Error)?.message || 'An error occurred while communicating with the server.'}
            </p>
          </div>
        </div>
      )}

      {/* Initial Loading */}
      {isInitialLoading ? (
        <div className="space-y-6">
          <CardSkeleton count={4} />
          <TableSkeleton rows={6} cols={6} />
        </div>
      ) : (
        <>
          {/* Top Statistics Cards */}
          <TrainingStats runs={runs} />

          {/* Toolbar */}
          <div className="bg-surface border border-border rounded-xl p-4 mb-6 shadow-sm">
            <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Search by run #, experiment, dataset, or model…"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-surface-2 border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
                {/* Status Filter */}
                <div className="flex items-center gap-1.5 min-w-[140px]">
                  <Filter className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-2.5 py-2 bg-surface-2 border border-border rounded-lg text-xs font-medium text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors cursor-pointer"
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Model Filter */}
                <div className="min-w-[150px]">
                  <select
                    value={modelFilter}
                    onChange={(e) => setModelFilter(e.target.value)}
                    className="w-full px-2.5 py-2 bg-surface-2 border border-border rounded-lg text-xs font-medium text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors cursor-pointer"
                  >
                    <option value="all">All Models</option>
                    {SUPPORTED_MODELS.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Clear filters button */}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="px-2.5 py-2 text-xs font-medium text-text-muted hover:text-text-primary rounded-lg hover:bg-surface-2 transition-colors whitespace-nowrap"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            </div>

            {/* Results Count Bar */}
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/60 text-xs text-text-muted">
              <span className="flex items-center gap-1.5 flex-wrap">
                <span>Showing</span>
                <strong className="text-text-primary font-semibold px-0.5">{filteredRuns.length}</strong>
                <span>of</span>
                <strong className="text-text-primary font-semibold px-0.5">{runs.length}</strong>
                <span>runs</span>
              </span>
              {hasActiveFilters && (
                <span className="text-accent-blue font-medium">Filtered results</span>
              )}
            </div>
          </div>

          {/* Content: Empty States or Global Run Table */}
          {runs.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-surface-2 flex items-center justify-center mb-4 text-accent-blue shadow-inner">
                <Brain className="w-7 h-7" />
              </div>
              <h3 className="text-base font-semibold text-text-primary mb-1">
                No Training Runs Found
              </h3>
              <p className="text-xs text-text-muted max-w-sm mb-6">
                No training runs have been created yet. Open an experiment and create a run to start training.
              </p>
              <Link
                to="/experiments"
                className="btn btn--primary inline-flex items-center gap-2 px-4 py-2 text-xs"
              >
                <FlaskConical className="w-4 h-4" /> Go to Experiments
              </Link>
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-xl bg-surface-2 flex items-center justify-center mb-3 text-text-muted">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                No runs match the selected filters
              </h3>
              <p className="text-xs text-text-muted max-w-xs mb-4">
                Try adjusting your search terms, status filter, or model filter.
              </p>
              <button
                onClick={clearFilters}
                className="btn btn--secondary text-xs px-3.5 py-1.5"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <GlobalRunTable
              runs={filteredRuns}
              experimentsMap={experimentsMap}
              datasetsMap={datasetsMap}
              onExecuteClick={(run) => setSelectedRunForExecute(run)}
              onQueueRun={handleQueueRun}
              onCancelRun={handleCancelRun}
              isActionLoading={
                queueMutation.isPending ||
                cancelMutation.isPending ||
                executeMutation.isPending
              }
            />
          )}
        </>
      )}

      {/* Execute Run Modal */}
      {selectedRunForExecute && (
        <ExecuteRunModal
          isOpen
          onClose={() => setSelectedRunForExecute(null)}
          onExecute={handleExecuteSubmit}
          isLoading={executeMutation.isPending}
          dataset={fullDataset}
        />
      )}
    </div>
  );
}
