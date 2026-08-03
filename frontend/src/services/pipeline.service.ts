/**
 * pipeline.service.ts — API client for Pipeline Visualization endpoints.
 */

import { get } from './api';
import type {
  LineageDataset,
  PipelineGraph,
  PipelineOverview,
  PipelineRunSummary,
  PipelineTimeline,
} from '@/types/pipeline.types';
import type { ApiResponse } from '@/types/api.types';

// ─── Service functions ────────────────────────────────────────────────────────

export async function getPipelineOverview(): Promise<ApiResponse<PipelineOverview>> {
  return get<PipelineOverview>('/pipeline/overview');
}

export async function getPipelineRuns(params?: {
  dataset_id?: string;
  experiment_id?: string;
  status?: string;
  model_type?: string;
}): Promise<ApiResponse<PipelineRunSummary[]>> {
  const query = new URLSearchParams();
  if (params?.dataset_id) query.set('dataset_id', params.dataset_id);
  if (params?.experiment_id) query.set('experiment_id', params.experiment_id);
  if (params?.status) query.set('status', params.status);
  if (params?.model_type) query.set('model_type', params.model_type);
  const qs = query.toString();
  const url = `/pipeline/runs${qs ? `?${qs}` : ''}`;
  return get<PipelineRunSummary[]>(url);
}

export async function getPipelineGraph(runId: string): Promise<
  ApiResponse<{ graph: PipelineGraph; timeline: PipelineTimeline }>
> {
  const res = (await get<PipelineGraph>(`/pipeline/${runId}`)) as unknown as { data: PipelineGraph; timeline: PipelineTimeline };
  const combined = res.data
    ? { graph: res.data, timeline: res.timeline }
    : null;
  return { data: combined, success: true, message: '', errors: null };
}

export async function getPipelineLineage(): Promise<ApiResponse<LineageDataset[]>> {
  return get<LineageDataset[]>('/pipeline/lineage');
}
