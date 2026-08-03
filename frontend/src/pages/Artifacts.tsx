import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  Download,
  Eye,
  ChevronRight,
  Package,
  HardDrive,
  Cpu,
  FileCode,
  Layers,
  FlaskConical,
  Database,
  X,
} from 'lucide-react';
import { useArtifacts, useArtifactStats } from '@/hooks/useArtifacts';
import { useExperiments, useRuns } from '@/hooks/useExperiments';
import { useDatasets } from '@/hooks/useDatasets';
import { ArtifactTypeBadge } from '@/components/artifacts/ArtifactTypeBadge';
import { ArtifactDetailModal } from '@/components/artifacts/ArtifactDetailModal';
import { CardSkeleton, TableSkeleton } from '@/components/common/LoadingSkeleton';
import { formatBytes } from '@/utils/format';
import { getArtifactDownloadUrl } from '@/services/artifact.service';
import type { Artifact } from '@/types/artifact.types';

const ARTIFACT_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'all', label: 'All Artifact Types' },
  { value: 'trained_model', label: 'Trained Models' },
  { value: 'metrics_json', label: 'Metrics JSON' },
  { value: 'evaluation_json', label: 'Evaluation JSON' },
  { value: 'confusion_matrix_json', label: 'Confusion Matrix JSON' },
  { value: 'configuration_json', label: 'Configuration JSON' },
  { value: 'preprocessing_json', label: 'Preprocessing Metadata' },
];

export function Artifacts() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [experimentFilter, setExperimentFilter] = useState<string>('all');
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);

  // Queries
  const {
    data: artifacts = [],
    isLoading: isLoadingArtifacts,
    error: artifactsError,
    refetch: refetchArtifacts,
    isRefetching: isRefetchingArtifacts,
  } = useArtifacts();

  const { data: stats } = useArtifactStats();
  const { data: experiments = [], isLoading: isLoadingExperiments } = useExperiments();
  const { data: runs = [], isLoading: isLoadingRuns } = useRuns();
  const { data: datasets = [] } = useDatasets();

  // Fast lookups
  const experimentsMap = useMemo(
    () => new Map(experiments.map((e) => [e.id, e])),
    [experiments]
  );
  const runsMap = useMemo(() => new Map(runs.map((r) => [r.id, r])), [runs]);
  const datasetsMap = useMemo(() => new Map(datasets.map((d) => [d.id, d])), [datasets]);

  // Filtered artifacts
  const filteredArtifacts = useMemo(() => {
    return artifacts.filter((art) => {
      // Type filter
      if (typeFilter !== 'all' && art.artifact_type !== typeFilter) {
        return false;
      }

      // Experiment filter
      if (experimentFilter !== 'all' && art.experiment_id !== experimentFilter) {
        return false;
      }

      // Search term
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase().trim();
        const exp = experimentsMap.get(art.experiment_id);
        const expName = exp?.name.toLowerCase() || '';
        const run = runsMap.get(art.run_id);
        const runNum = run ? `#${run.run_number}`.toLowerCase() : '';
        const dataset = datasetsMap.get(art.dataset_id);
        const datasetName = dataset?.name.toLowerCase() || '';

        const matches =
          art.filename.toLowerCase().includes(term) ||
          art.artifact_type.toLowerCase().includes(term) ||
          art.id.toLowerCase().includes(term) ||
          art.run_id.toLowerCase().includes(term) ||
          runNum.includes(term) ||
          expName.includes(term) ||
          datasetName.includes(term);

        if (!matches) return false;
      }

      return true;
    });
  }, [artifacts, typeFilter, experimentFilter, searchTerm, experimentsMap, runsMap, datasetsMap]);

  const clearFilters = () => {
    setSearchTerm('');
    setTypeFilter('all');
    setExperimentFilter('all');
  };

  const hasActiveFilters =
    searchTerm.trim() !== '' || typeFilter !== 'all' || experimentFilter !== 'all';

  const isInitialLoading = isLoadingArtifacts || isLoadingExperiments || isLoadingRuns;

  // Computed summary metrics
  const totalCount = stats?.total_artifacts ?? artifacts.length;
  const modelsCount =
    stats?.models_stored ??
    artifacts.filter((a) => a.artifact_type === 'trained_model').length;
  const jsonCount =
    stats?.json_reports ??
    artifacts.filter((a) => a.artifact_type !== 'trained_model').length;
  const totalSizeBytes =
    stats?.total_size_bytes ??
    artifacts.reduce((acc, a) => acc + (a.file_size_bytes || 0), 0);

  return (
    <div className="page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Artifact Registry
          </h1>
          <p className="text-sm text-text-muted mt-0.5">
            Immutable model artifacts, metrics reports, and training snapshots
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => refetchArtifacts()}
            disabled={isRefetchingArtifacts}
            className="px-3 py-2 text-xs font-medium text-text-muted hover:text-text-primary border border-border rounded-lg bg-surface hover:bg-surface-2 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            title="Refresh artifacts"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isRefetchingArtifacts ? 'animate-spin text-accent-blue' : ''}`}
            />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {artifactsError && (
        <div className="p-4 mb-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold mb-0.5">Failed to load artifacts</h4>
            <p className="text-xs opacity-90">
              {(artifactsError as Error)?.message || 'An error occurred while communicating with the server.'}
            </p>
          </div>
        </div>
      )}

      {/* Initial Loading */}
      {isInitialLoading ? (
        <div className="space-y-6">
          <CardSkeleton count={4} />
          <TableSkeleton rows={6} cols={7} />
        </div>
      ) : (
        <>
          {/* Top Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-surface border border-border rounded-xl p-4 shadow-sm flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-medium text-text-muted uppercase tracking-wider block">
                  Total Artifacts
                </span>
                <span className="text-2xl font-bold font-mono text-text-primary">
                  {totalCount}
                </span>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-xl p-4 shadow-sm flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-medium text-text-muted uppercase tracking-wider block">
                  Models Stored
                </span>
                <span className="text-2xl font-bold font-mono text-text-primary">
                  {modelsCount}
                </span>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-xl p-4 shadow-sm flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <FileCode className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-medium text-text-muted uppercase tracking-wider block">
                  JSON Reports
                </span>
                <span className="text-2xl font-bold font-mono text-text-primary">
                  {jsonCount}
                </span>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-xl p-4 shadow-sm flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <HardDrive className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-medium text-text-muted uppercase tracking-wider block">
                  Storage Used
                </span>
                <span className="text-2xl font-bold font-mono text-text-primary">
                  {formatBytes(totalSizeBytes)}
                </span>
              </div>
            </div>
          </div>

          {/* Toolbar */}
          <div className="bg-surface border border-border rounded-xl p-4 mb-6 shadow-sm">
            <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Search by filename, run #, experiment, or type…"
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
                {/* Artifact Type Filter */}
                <div className="flex items-center gap-1.5 min-w-[160px]">
                  <Filter className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="w-full px-2.5 py-2 bg-surface-2 border border-border rounded-lg text-xs font-medium text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors cursor-pointer"
                  >
                    {ARTIFACT_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Experiment Filter */}
                <div className="min-w-[160px]">
                  <select
                    value={experimentFilter}
                    onChange={(e) => setExperimentFilter(e.target.value)}
                    className="w-full px-2.5 py-2 bg-surface-2 border border-border rounded-lg text-xs font-medium text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors cursor-pointer"
                  >
                    <option value="all">All Experiments</option>
                    {experiments.map((exp) => (
                      <option key={exp.id} value={exp.id}>
                        {exp.name}
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
              <span>
                Showing <strong className="text-text-primary">{filteredArtifacts.length}</strong> of{' '}
                <strong className="text-text-primary">{artifacts.length}</strong> artifacts
              </span>
              {hasActiveFilters && (
                <span className="text-accent-blue font-medium">Filtered results</span>
              )}
            </div>
          </div>

          {/* Table or Empty States */}
          {artifacts.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-surface-2 flex items-center justify-center mb-4 text-accent-blue shadow-inner">
                <Package className="w-7 h-7" />
              </div>
              <h3 className="text-base font-semibold text-text-primary mb-1">
                No Artifacts Stored Yet
              </h3>
              <p className="text-xs text-text-muted max-w-sm mb-6">
                Trained models, metrics reports, and evaluation summaries will automatically be recorded here after training runs complete.
              </p>
              <Link
                to="/training"
                className="btn btn--primary inline-flex items-center gap-2 px-4 py-2 text-xs"
              >
                <Cpu className="w-4 h-4" /> Go to Training Operations
              </Link>
            </div>
          ) : filteredArtifacts.length === 0 ? (
            <div className="bg-surface border border-border rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-xl bg-surface-2 flex items-center justify-center mb-3 text-text-muted">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                No artifacts match the selected filters
              </h3>
              <p className="text-xs text-text-muted max-w-xs mb-4">
                Try adjusting your search terms, artifact type, or experiment filter.
              </p>
              <button
                onClick={clearFilters}
                className="btn btn--secondary text-xs px-3.5 py-1.5"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[850px]">
                  <thead>
                    <tr className="bg-surface-2 border-b border-border text-xs font-semibold uppercase tracking-wider text-text-muted">
                      <th className="px-4 py-3.5">Artifact</th>
                      <th className="px-4 py-3.5">Type</th>
                      <th className="px-4 py-3.5">Run</th>
                      <th className="px-4 py-3.5">Experiment</th>
                      <th className="px-4 py-3.5">Dataset</th>
                      <th className="px-4 py-3.5">File Size</th>
                      <th className="px-4 py-3.5">Created</th>
                      <th className="px-4 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-sm">
                    {filteredArtifacts.map((art) => {
                      const exp = experimentsMap.get(art.experiment_id);
                      const run = runsMap.get(art.run_id);
                      const dataset = datasetsMap.get(art.dataset_id);
                      const downloadUrl = getArtifactDownloadUrl(art.id);

                      return (
                        <tr
                          key={art.id}
                          className="hover:bg-surface-2/60 transition-colors group"
                        >
                          {/* Filename */}
                          <td className="px-4 py-3.5">
                            <button
                              onClick={() => setSelectedArtifact(art)}
                              className="font-medium text-text-primary hover:text-accent-blue transition-colors flex items-center gap-2 text-left"
                            >
                              <FileCode className="w-4 h-4 text-text-muted shrink-0" />
                              <span className="font-mono text-xs">{art.filename}</span>
                            </button>
                          </td>

                          {/* Type */}
                          <td className="px-4 py-3.5 whitespace-nowrap">
                            <ArtifactTypeBadge type={art.artifact_type} size="sm" />
                          </td>

                          {/* Run */}
                          <td className="px-4 py-3.5 whitespace-nowrap">
                            {run ? (
                              <Link
                                to={`/runs/${run.id}`}
                                className="font-mono text-xs font-bold text-text-primary hover:text-accent-blue transition-colors"
                              >
                                #{run.run_number}
                              </Link>
                            ) : (
                              <Link
                                to={`/runs/${art.run_id}`}
                                className="font-mono text-xs text-text-muted hover:text-accent-blue transition-colors"
                              >
                                {art.run_id.slice(0, 8)}…
                              </Link>
                            )}
                          </td>

                          {/* Experiment */}
                          <td className="px-4 py-3.5">
                            {exp ? (
                              <Link
                                to={`/experiments/${exp.id}`}
                                className="text-xs font-medium text-text-primary hover:text-accent-blue transition-colors flex items-center gap-1.5 truncate max-w-[160px]"
                                title={exp.name}
                              >
                                <FlaskConical className="w-3.5 h-3.5 text-text-muted shrink-0" />
                                <span className="truncate">{exp.name}</span>
                              </Link>
                            ) : (
                              <span className="text-xs font-mono text-text-muted">
                                {art.experiment_id.slice(0, 8)}…
                              </span>
                            )}
                          </td>

                          {/* Dataset */}
                          <td className="px-4 py-3.5">
                            {dataset ? (
                              <Link
                                to={`/datasets/${dataset.id}`}
                                className="text-xs font-medium text-text-secondary hover:text-accent-blue transition-colors inline-flex items-center gap-1 bg-surface-2 px-2 py-0.5 rounded border border-border truncate max-w-[140px]"
                                title={dataset.name}
                              >
                                <Database className="w-3 h-3 text-text-muted shrink-0" />
                                <span className="truncate">{dataset.name}</span>
                              </Link>
                            ) : (
                              <span className="text-xs text-text-muted">—</span>
                            )}
                          </td>

                          {/* File Size */}
                          <td className="px-4 py-3.5 text-xs font-mono text-text-secondary whitespace-nowrap">
                            {formatBytes(art.file_size_bytes)}
                          </td>

                          {/* Created */}
                          <td className="px-4 py-3.5 text-xs text-text-muted whitespace-nowrap">
                            {new Date(art.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3.5 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end gap-1">
                              {/* View Metadata */}
                              <button
                                onClick={() => setSelectedArtifact(art)}
                                title="View Metadata"
                                className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                              >
                                <Eye className="w-4 h-4" />
                              </button>

                              {/* Download */}
                              <a
                                href={downloadUrl}
                                download={art.filename}
                                title="Download Artifact"
                                className="p-1.5 rounded text-text-muted hover:text-accent-blue hover:bg-accent-blue/10 transition-colors inline-flex items-center"
                              >
                                <Download className="w-4 h-4" />
                              </a>

                              {/* Navigate to Run */}
                              <button
                                onClick={() => navigate(`/runs/${art.run_id}`)}
                                title="Go to Run"
                                className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                              >
                                <ChevronRight className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Artifact Metadata Modal */}
      {selectedArtifact && (
        <ArtifactDetailModal
          isOpen
          onClose={() => setSelectedArtifact(null)}
          artifact={selectedArtifact}
          experiment={experimentsMap.get(selectedArtifact.experiment_id)}
          dataset={datasetsMap.get(selectedArtifact.dataset_id)}
        />
      )}
    </div>
  );
}
