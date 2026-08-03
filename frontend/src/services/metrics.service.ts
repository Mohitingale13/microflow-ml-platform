/**
 * metrics.service.ts — API client calls for the Metrics Dashboard.
 */

import { get } from './api';
import type { ApiResponse } from '@/types/api.types';
import type {
  DatasetMetricSummary,
  ExperimentMetricSummary,
  MetricsOverview,
  ModelMetricSummary,
  RunComparisonItem,
} from '@/types/metrics.types';

export async function getMetricsOverview(): Promise<ApiResponse<MetricsOverview>> {
  return get<MetricsOverview>('/metrics/overview');
}

export async function getModelMetrics(params?: {
  dataset_id?: string;
  experiment_id?: string;
}): Promise<ApiResponse<ModelMetricSummary[]>> {
  const queryParams = new URLSearchParams();
  if (params?.dataset_id && params.dataset_id !== 'all') {
    queryParams.append('dataset_id', params.dataset_id);
  }
  if (params?.experiment_id && params.experiment_id !== 'all') {
    queryParams.append('experiment_id', params.experiment_id);
  }
  const qs = queryParams.toString();
  return get<ModelMetricSummary[]>(`/metrics/models${qs ? `?${qs}` : ''}`);
}

export async function getExperimentMetrics(params?: {
  dataset_id?: string;
  model_type?: string;
}): Promise<ApiResponse<ExperimentMetricSummary[]>> {
  const queryParams = new URLSearchParams();
  if (params?.dataset_id && params.dataset_id !== 'all') {
    queryParams.append('dataset_id', params.dataset_id);
  }
  if (params?.model_type && params.model_type !== 'all') {
    queryParams.append('model_type', params.model_type);
  }
  const qs = queryParams.toString();
  return get<ExperimentMetricSummary[]>(`/metrics/experiments${qs ? `?${qs}` : ''}`);
}

export async function getDatasetMetrics(): Promise<ApiResponse<DatasetMetricSummary[]>> {
  return get<DatasetMetricSummary[]>('/metrics/datasets');
}

export async function compareRuns(runIds: string[]): Promise<ApiResponse<RunComparisonItem[]>> {
  if (!runIds || runIds.length === 0) {
    return { success: true, message: 'No runs to compare', data: [], errors: null };
  }
  const ids = runIds.join(',');
  return get<RunComparisonItem[]>(`/metrics/runs/compare?run_ids=${encodeURIComponent(ids)}`);
}
