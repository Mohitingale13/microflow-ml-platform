// useAIReview.ts — TanStack Query hook for the AI Run Review feature.

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateRunReview } from '../services/ai.service';
import type { AIReviewResponse } from '../types/ai.types';

/**
 * Mutation hook for generating (or retrieving cached) an AI review.
 *
 * Uses a mutation because the endpoint is POST and has side effects
 * (may call Gemini and write to the database). The result is cached in
 * TanStack Query under ['ai-review', runId] after the first successful call.
 */
export function useGenerateAIReview(runId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateRunReview(runId),
    onSuccess: (data) => {
      if (data.success && data.data) {
        // Cache the result so the component can read it instantly on re-render
        queryClient.setQueryData<AIReviewResponse>(['ai-review', runId], data.data);
      }
    },
  });
}
