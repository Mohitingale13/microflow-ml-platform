// ai.service.ts — Frontend API client for AI Review, Comparison, and Ask MicroFlow endpoints.

import { get, post } from './api';
import type { ApiResponse } from '@/types/api.types';
import type { 
  AIReviewResponse, 
  AIComparisonResponse, 
  AIQueryResponse, 
  ConversationMessage 
} from '@/types/ai.types';

/**
 * POST /api/v1/runs/{runId}/review
 * Triggers review generation on the backend.
 */
export async function generateRunReview(
  runId: string
): Promise<ApiResponse<AIReviewResponse>> {
  return post<AIReviewResponse, Record<string, never>>(
    `/runs/${runId}/review`,
    {}
  );
}

/**
 * POST /api/v1/runs/compare
 * Triggers an AI comparison of two completed runs from the same experiment.
 */
export async function compareRuns(
  runAId: string,
  runBId: string
): Promise<ApiResponse<AIComparisonResponse>> {
  return post<AIComparisonResponse, { run_a_id: string; run_b_id: string }>(
    `/runs/compare`,
    { run_a_id: runAId, run_b_id: runBId }
  );
}

// ─── Ask MicroFlow (Natural Language Assistant) ────────────────────────────────

/**
 * POST /api/v1/assistant/query
 * Send a natural language ML platform query to Ask MicroFlow with session context.
 */
export async function askAssistant(
  question: string,
  context?: ConversationMessage[]
): Promise<ApiResponse<AIQueryResponse>> {
  return post<AIQueryResponse, { question: string; context?: ConversationMessage[] }>(
    `/assistant/query`,
    { question, context }
  );
}

/**
 * GET /api/v1/assistant/recent
 * Retrieve recent cached assistant queries.
 */
export async function getRecentQueries(
  limit = 10
): Promise<ApiResponse<AIQueryResponse[]>> {
  return get<AIQueryResponse[]>(`/assistant/recent?limit=${limit}`);
}

/**
 * GET /api/v1/assistant/suggestions
 * Retrieve domain suggested questions for the interactive search interface.
 */
export async function getSuggestedQuestions(): Promise<ApiResponse<string[]>> {
  return get<string[]>(`/assistant/suggestions`);
}
