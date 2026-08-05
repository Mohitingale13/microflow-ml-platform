// dataset-ai.service.ts — Frontend API client for AI Dataset Intelligence endpoint.

import { post } from './api';
import type { ApiResponse } from '@/types/api.types';
import type { DatasetAIAnalysis } from '@/types/dataset-ai.types';

/**
 * POST /api/v1/datasets/{datasetId}/analyze
 * Triggers AI Dataset Intelligence analysis generation or retrieves cached report.
 */
export async function analyzeDataset(
  datasetId: string
): Promise<ApiResponse<DatasetAIAnalysis>> {
  return post<DatasetAIAnalysis, Record<string, never>>(
    `/datasets/${datasetId}/analyze`,
    {}
  );
}
