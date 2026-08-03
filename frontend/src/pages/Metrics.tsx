/**
 * Metrics.tsx — Historical Experiment Analytics & Performance Dashboard.
 */

import { useState, useMemo } from 'react';
import {
  BarChart3,
  RefreshCw,
  Search,
  SlidersHorizontal,
  X,
  Award,
  FlaskConical,
  Database,
  TrendingUp,
} from 'lucide-react';
import {
  useDatasetMetrics,
  useExperimentMetrics,
  useMetricsOverview,
  useModelMetrics,
} from '@/hooks/useMetrics';
import { useDatasets } from '@/hooks/useDatasets';
import { useExperiments, useRuns } from '@/hooks/useExperiments';
import { MetricsOverviewCards } from '@/components/metrics/MetricsOverviewCards';
import { MetricsCharts } from '@/components/metrics/MetricsCharts';
import { ModelLeaderboardTable } from '@/components/metrics/ModelLeaderboardTable';
import { ExperimentAnalyticsTable } from '@/components/metrics/ExperimentAnalyticsTable';
import { DatasetAnalyticsTable } from '@/components/metrics/DatasetAnalyticsTable';
import { RunComparisonSection } from '@/components/metrics/RunComparisonSection';
import type {
  DatasetMetricSummary,
  ExperimentMetricSummary,
  ModelMetricSummary,
} from '@/types/metrics.types';

type ActiveViewTab = 'overview' | 'leaderboard' | 'experiments' | 'datasets' | 'compare';

export function Metrics() {
  // Navigation tab state
  const [activeTab, setActiveTab] = useState<ActiveViewTab>('overview');

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('all');
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>('all');
  const [selectedModelType, setSelectedModelType] = useState<string>('all');

  // Queries
  const {
    data: overview,
    isLoading: isLoadingOverview,
    refetch: refetchOverview,
    isRefetching: isRefetchingOverview,
  } = useMetricsOverview();

  const {
    data: rawModelMetrics = [],
    isLoading: isLoadingModels,
    refetch: refetchModels,
  } = useModelMetrics({
    dataset_id: selectedDatasetId !== 'all' ? selectedDatasetId : undefined,
    experiment_id: selectedExperimentId !== 'all' ? selectedExperimentId : undefined,
  });

  const {
    data: rawExperimentMetrics = [],
    isLoading: isLoadingExperiments,
    refetch: refetchExperiments,
  } = useExperimentMetrics({
    dataset_id: selectedDatasetId !== 'all' ? selectedDatasetId : undefined,
    model_type: selectedModelType !== 'all' ? selectedModelType : undefined,
  });

  const {
    data: rawDatasetMetrics = [],
    isLoading: isLoadingDatasets,
    refetch: refetchDatasets,
  } = useDatasetMetrics();

  // Reference queries for filter dropdowns & run comparison
  const { data: datasets = [] } = useDatasets();
  const { data: experiments = [] } = useExperiments();
  const { data: runs = [] } = useRuns();

  const experimentNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const e of experiments) {
      map[e.id] = e.name;
    }
    return map;
  }, [experiments]);

  // Client-side search filtering across dataset/experiment/model tables
  const filteredModelMetrics: ModelMetricSummary[] = useMemo(() => {
    if (!searchTerm.trim()) return rawModelMetrics;
    const term = searchTerm.toLowerCase();
    return rawModelMetrics.filter((m: ModelMetricSummary) =>
      m.model_type.toLowerCase().includes(term)
    );
  }, [rawModelMetrics, searchTerm]);

  const filteredExperimentMetrics: ExperimentMetricSummary[] = useMemo(() => {
    let list: ExperimentMetricSummary[] = rawExperimentMetrics;
    if (selectedExperimentId !== 'all') {
      list = list.filter((e: ExperimentMetricSummary) => e.experiment_id === selectedExperimentId);
    }
    if (!searchTerm.trim()) return list;
    const term = searchTerm.toLowerCase();
    return list.filter(
      (e: ExperimentMetricSummary) =>
        e.experiment_name.toLowerCase().includes(term) ||
        (e.dataset_name && e.dataset_name.toLowerCase().includes(term))
    );
  }, [rawExperimentMetrics, selectedExperimentId, searchTerm]);

  const filteredDatasetMetrics: DatasetMetricSummary[] = useMemo(() => {
    let list: DatasetMetricSummary[] = rawDatasetMetrics;
    if (selectedDatasetId !== 'all') {
      list = list.filter((d: DatasetMetricSummary) => d.dataset_id === selectedDatasetId);
    }
    if (!searchTerm.trim()) return list;
    const term = searchTerm.toLowerCase();
    return list.filter((d: DatasetMetricSummary) => d.dataset_name.toLowerCase().includes(term));
  }, [rawDatasetMetrics, selectedDatasetId, searchTerm]);

  const handleRefreshAll = () => {
    refetchOverview();
    refetchModels();
    refetchExperiments();
    refetchDatasets();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedDatasetId('all');
    setSelectedExperimentId('all');
    setSelectedModelType('all');
  };

  const hasActiveFilters =
    searchTerm.trim() !== '' ||
    selectedDatasetId !== 'all' ||
    selectedExperimentId !== 'all' ||
    selectedModelType !== 'all';

  return (
    <div className="page space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="page-title text-2xl font-bold flex items-center gap-2.5">
              <BarChart3 className="text-primary" size={24} />
              Metrics & Analytics
            </h1>
          </div>
          <p className="page-subtitle text-xs text-muted-foreground mt-1">
            Historical experiment benchmarks and model performance analytics from persisted RunResults
          </p>
        </div>

        <button
          onClick={handleRefreshAll}
          disabled={isRefetchingOverview}
          className="btn btn-outline text-xs self-start md:self-auto flex items-center gap-1.5"
        >
          <RefreshCw size={13} className={isRefetchingOverview ? 'animate-spin' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Section 1: Global Overview Metric Cards */}
      <MetricsOverviewCards overview={overview} isLoading={isLoadingOverview} />

      {/* Global Filter Toolbar */}
      <div className="card p-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
            <input
              type="text"
              placeholder="Search by experiment, dataset, or model family..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-9 text-xs w-full"
            />
          </div>

          {/* Dataset Filter */}
          <div className="flex items-center gap-2 min-w-[170px]">
            <Database size={13} className="text-muted-foreground shrink-0" />
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="input text-xs w-full py-1.5"
            >
              <option value="all">All Datasets</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Experiment Filter */}
          <div className="flex items-center gap-2 min-w-[180px]">
            <FlaskConical size={13} className="text-muted-foreground shrink-0" />
            <select
              value={selectedExperimentId}
              onChange={(e) => setSelectedExperimentId(e.target.value)}
              className="input text-xs w-full py-1.5"
            >
              <option value="all">All Experiments</option>
              {experiments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          </div>

          {/* Model Filter */}
          <div className="flex items-center gap-2 min-w-[170px]">
            <SlidersHorizontal size={13} className="text-muted-foreground shrink-0" />
            <select
              value={selectedModelType}
              onChange={(e) => setSelectedModelType(e.target.value)}
              className="input text-xs w-full py-1.5"
            >
              <option value="all">All Models</option>
              <option value="random_forest">Random Forest</option>
              <option value="logistic_regression">Logistic Regression</option>
              <option value="xgboost">XGBoost</option>
            </select>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="btn btn-ghost text-xs px-2.5 py-1.5 text-muted-foreground hover:text-foreground shrink-0 flex items-center gap-1"
            >
              <X size={13} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Navigation View Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2 overflow-x-auto text-xs">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'overview'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          }`}
        >
          <BarChart3 size={14} />
          <span>Visual Charts</span>
        </button>

        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'leaderboard'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          }`}
        >
          <Award size={14} />
          <span>Model Leaderboard</span>
          {filteredModelMetrics.length > 0 && (
            <span className="bg-primary-foreground/20 text-primary-foreground text-[10px] px-1.5 py-0.2 rounded-full font-mono">
              {filteredModelMetrics.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('experiments')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'experiments'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          }`}
        >
          <FlaskConical size={14} />
          <span>Experiment Analytics</span>
          {filteredExperimentMetrics.length > 0 && (
            <span className="bg-primary-foreground/20 text-primary-foreground text-[10px] px-1.5 py-0.2 rounded-full font-mono">
              {filteredExperimentMetrics.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('datasets')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'datasets'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          }`}
        >
          <Database size={14} />
          <span>Dataset Analytics</span>
          {filteredDatasetMetrics.length > 0 && (
            <span className="bg-primary-foreground/20 text-primary-foreground text-[10px] px-1.5 py-0.2 rounded-full font-mono">
              {filteredDatasetMetrics.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('compare')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'compare'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          }`}
        >
          <TrendingUp size={14} />
          <span>Run Comparison</span>
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <MetricsCharts
            overview={overview}
            modelMetrics={filteredModelMetrics}
            experimentMetrics={filteredExperimentMetrics}
          />
          <ModelLeaderboardTable
            models={filteredModelMetrics}
            isLoading={isLoadingModels}
          />
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <ModelLeaderboardTable
          models={filteredModelMetrics}
          isLoading={isLoadingModels}
        />
      )}

      {activeTab === 'experiments' && (
        <ExperimentAnalyticsTable
          experiments={filteredExperimentMetrics}
          isLoading={isLoadingExperiments}
        />
      )}

      {activeTab === 'datasets' && (
        <DatasetAnalyticsTable
          datasets={filteredDatasetMetrics}
          isLoading={isLoadingDatasets}
        />
      )}

      {activeTab === 'compare' && (
        <RunComparisonSection
          availableRuns={runs}
          experimentNames={experimentNameMap}
        />
      )}
    </div>
  );
}
