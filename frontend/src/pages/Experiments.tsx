import { useState, useMemo } from 'react';
import { Plus, Search, SlidersHorizontal } from 'lucide-react';
import { useExperiments } from '../hooks/useExperiments';
import { useDatasets } from '../hooks/useDatasets';
import { ExperimentTable } from '../components/experiments/ExperimentTable';
import { CreateExperimentModal } from '../components/experiments/CreateExperimentModal';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import type { ExperimentListItem } from '../types/experiment.types';

type StatusFilter = 'all' | 'draft' | 'active' | 'archived';

export function Experiments() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const { data: experiments = [], isLoading, error } = useExperiments();
  const { data: datasets = [] } = useDatasets();

  const datasetOptions = useMemo(
    () => datasets.map((d) => ({ id: d.id, name: d.name })),
    [datasets]
  );

  const filtered = useMemo(() => {
    let list: ExperimentListItem[] = experiments;
    if (statusFilter !== 'all') {
      list = list.filter((e) => e.status === statusFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (e) =>
          e.name.toLowerCase().includes(q) ||
          e.description?.toLowerCase().includes(q) ||
          e.objective?.toLowerCase().includes(q) ||
          e.tags?.some((t) => t.toLowerCase().includes(q))
      );
    }
    return list;
  }, [experiments, statusFilter, search]);

  const counts: Record<string, number> = useMemo(() => {
    return { all: experiments.length, ...Object.fromEntries(
      ['draft', 'active', 'archived'].map((s) => [
        s, experiments.filter((e) => e.status === s).length,
      ])
    ) };
  }, [experiments]);

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Experiments</h2>
          <p className="page-subtitle">Design, organize, and manage ML experiments</p>
        </div>
        <button
          id="create-experiment-btn"
          onClick={() => setIsCreateOpen(true)}
          className="btn btn--primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Experiment
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {([
          { label: 'Total', key: 'all', color: 'text-text-primary' },
          { label: 'Active', key: 'active', color: 'text-accent-blue' },
          { label: 'Draft', key: 'draft', color: 'text-text-muted' },
          { label: 'Archived', key: 'archived', color: 'text-accent-purple' },
        ] as const).map(({ label, key, color }) => (
          <button
            key={key}
            onClick={() => setStatusFilter(key)}
            className={`block bg-surface border rounded-lg p-4 text-left transition-all ${
              statusFilter === key
                ? 'border-accent-blue shadow-[0_0_0_1px_rgba(59,130,246,0.3)]'
                : 'border-border hover:border-border-2'
            }`}
          >
            <p className="text-xs text-text-muted mb-1 font-medium uppercase tracking-wider">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{counts[key] ?? 0}</p>
          </button>
        ))}
      </div>

      {/* Search & Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
          <input
            id="experiments-search"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, description, objective or tag…"
            className="w-full pl-9 pr-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-text-muted shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary focus:outline-none focus:border-accent-blue transition-colors"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {error ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          Failed to load experiments: {(error as Error).message}
        </div>
      ) : isLoading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : (
        <>
          {search && (
            <p className="text-xs text-text-muted mb-3">
              {filtered.length} result{filtered.length !== 1 ? 's' : ''} for "{search}"
            </p>
          )}
          <ExperimentTable data={filtered} />
        </>
      )}

      <CreateExperimentModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        datasets={datasetOptions}
      />
    </div>
  );
}
