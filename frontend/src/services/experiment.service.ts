import { get, post } from './api';
import type { ApiResponse } from '@/types/api.types';
import type {
  Experiment,
  ExperimentCreate,
  ExperimentListItem,
  ExperimentUpdate,
  Run,
  RunCreate,
  RunListItem,
  RunUpdate,
} from '@/types/experiment.types';
import apiClient from './api';

// ─── Experiment API ────────────────────────────────────────────────────────────

export async function getExperiments(): Promise<ApiResponse<ExperimentListItem[]>> {
  return get<ExperimentListItem[]>('/experiments');
}

export async function getExperiment(id: string): Promise<ApiResponse<Experiment>> {
  return get<Experiment>(`/experiments/${id}`);
}

export async function createExperiment(
  payload: ExperimentCreate
): Promise<ApiResponse<Experiment>> {
  return post<Experiment, ExperimentCreate>('/experiments', payload);
}

export async function updateExperiment(
  id: string,
  payload: ExperimentUpdate
): Promise<ApiResponse<Experiment>> {
  const response = await apiClient.put<ApiResponse<Experiment>>(
    `/experiments/${id}`,
    payload
  );
  return response.data;
}

export async function deleteExperiment(id: string): Promise<ApiResponse<null>> {
  const response = await apiClient.delete<ApiResponse<null>>(`/experiments/${id}`);
  return response.data;
}

export async function getExperimentRuns(
  experimentId: string
): Promise<ApiResponse<RunListItem[]>> {
  return get<RunListItem[]>(`/experiments/${experimentId}/runs`);
}

// ─── Run API ───────────────────────────────────────────────────────────────────

export async function getRuns(): Promise<ApiResponse<RunListItem[]>> {
  return get<RunListItem[]>('/runs');
}

export async function getRun(id: string): Promise<ApiResponse<Run>> {
  return get<Run>(`/runs/${id}`);
}

export async function createRun(payload: RunCreate): Promise<ApiResponse<Run>> {
  return post<Run, RunCreate>('/runs', payload);
}

export async function updateRun(
  id: string,
  payload: RunUpdate
): Promise<ApiResponse<Run>> {
  const response = await apiClient.put<ApiResponse<Run>>(`/runs/${id}`, payload);
  return response.data;
}

export async function deleteRun(id: string): Promise<ApiResponse<null>> {
  const response = await apiClient.delete<ApiResponse<null>>(`/runs/${id}`);
  return response.data;
}

export async function queueRun(id: string): Promise<ApiResponse<Run>> {
  return post<Run, null>(`/runs/${id}/queue`, null);
}

export async function cancelRun(id: string): Promise<ApiResponse<Run>> {
  return post<Run, null>(`/runs/${id}/cancel`, null);
}

export async function executeRun(
  id: string,
  payload: { target_column: string; test_split?: number }
): Promise<ApiResponse<import('@/types/experiment.types').ExecuteRunResponse>> {
  return post<import('@/types/experiment.types').ExecuteRunResponse, typeof payload>(
    `/runs/${id}/execute`,
    payload
  );
}

export async function getRunResult(
  runId: string
): Promise<ApiResponse<import('@/types/artifact.types').RunResult | null>> {
  return get<import('@/types/artifact.types').RunResult | null>(`/runs/${runId}/result`);
}

export async function getRunArtifacts(
  runId: string
): Promise<ApiResponse<import('@/types/artifact.types').Artifact[]>> {
  return get<import('@/types/artifact.types').Artifact[]>(`/runs/${runId}/artifacts`);
}
