/**
 * useMetrics.ts — TanStack Query hooks for experiment analytics and metrics.
 */

import { useQuery } from '@tanstack/react-query';
import {
  compareRuns,
  getDatasetMetrics,
  getExperimentMetrics,
  getMetricsOverview,
  getModelMetrics,
} from '@/services/metrics.service';
import type {
  DatasetMetricSummary,
  ExperimentMetricSummary,
  MetricsOverview,
  ModelMetricSummary,
  RunComparisonItem,
} from '@/types/metrics.types';

export function useMetricsOverview() {
  return useQuery<MetricsOverview, Error>({
    queryKey: ['metrics', 'overview'],
    queryFn: async (): Promise<MetricsOverview> => {
      const response = await getMetricsOverview();
      if (!response.data) {
        return {
          total_runs: 0,
          completed_runs: 0,
          failed_runs: 0,
          success_rate: 0.0,
          average_accuracy: null,
          average_precision: null,
          average_recall: null,
          average_f1: null,
          average_roc_auc: null,
          average_training_duration: null,
        };
      }
      return response.data;
    },
    refetchInterval: 10000,
  });
}

export function useModelMetrics(params?: {
  dataset_id?: string;
  experiment_id?: string;
}) {
  return useQuery<ModelMetricSummary[], Error>({
    queryKey: ['metrics', 'models', params?.dataset_id, params?.experiment_id],
    queryFn: async (): Promise<ModelMetricSummary[]> => {
      const response = await getModelMetrics(params);
      return response.data ?? [];
    },
  });
}

export function useExperimentMetrics(params?: {
  dataset_id?: string;
  model_type?: string;
}) {
  return useQuery<ExperimentMetricSummary[], Error>({
    queryKey: ['metrics', 'experiments', params?.dataset_id, params?.model_type],
    queryFn: async (): Promise<ExperimentMetricSummary[]> => {
      const response = await getExperimentMetrics(params);
      return response.data ?? [];
    },
  });
}

export function useDatasetMetrics() {
  return useQuery<DatasetMetricSummary[], Error>({
    queryKey: ['metrics', 'datasets'],
    queryFn: async (): Promise<DatasetMetricSummary[]> => {
      const response = await getDatasetMetrics();
      return response.data ?? [];
    },
  });
}

export function useRunComparison(runIds: string[]) {
  return useQuery<RunComparisonItem[], Error>({
    queryKey: ['metrics', 'compare', runIds.slice().sort().join(',')],
    queryFn: async (): Promise<RunComparisonItem[]> => {
      if (!runIds || runIds.length === 0) return [];
      const response = await compareRuns(runIds);
      return response.data ?? [];
    },
    enabled: runIds.length > 0,
  });
}
