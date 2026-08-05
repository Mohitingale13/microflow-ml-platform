// experiment-strategy.service.ts — Frontend API client for AI Experiment Strategy endpoint.

import { post } from './api';
import type { ApiResponse } from '@/types/api.types';
import type { ExperimentStrategy } from '@/types/experiment-strategy.types';

/**
 * POST /api/v1/experiments/{experimentId}/strategy
 * Triggers AI Experiment Strategy analysis generation or retrieves cached recommendation report.
 */
export async function generateExperimentStrategy(
  experimentId: string
): Promise<ApiResponse<ExperimentStrategy>> {
  return post<ExperimentStrategy, Record<string, never>>(
    `/experiments/${experimentId}/strategy`,
    {}
  );
}
