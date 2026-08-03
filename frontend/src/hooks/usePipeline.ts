/**
 * usePipeline.ts — TanStack Query hooks for the Pipeline Visualization module.
 */

import { useQuery } from '@tanstack/react-query';
import {
  getPipelineGraph,
  getPipelineLineage,
  getPipelineOverview,
  getPipelineRuns,
} from '@/services/pipeline.service';
import type {
  LineageDataset,
  PipelineOverview,
  PipelineRunSummary,
} from '@/types/pipeline.types';

// ─── Hooks ────────────────────────────────────────────────────────────────────

export function usePipelineOverview() {
  return useQuery({
    queryKey: ['pipeline-overview'],
    queryFn: async (): Promise<PipelineOverview> => {
      const res = await getPipelineOverview();
      if (!res.data) {
        return {
          total_pipelines: 0,
          running: 0,
          completed: 0,
          failed: 0,
          queued: 0,
          draft: 0,
          average_duration_seconds: null,
          total_artifacts_produced: 0,
          success_rate: 0.0,
        };
      }
      return res.data;
    },
    refetchInterval: 15_000, // auto-refresh every 15s
  });
}

export function usePipelineRuns(params?: {
  dataset_id?: string;
  experiment_id?: string;
  status?: string;
  model_type?: string;
}) {
  return useQuery<PipelineRunSummary[], Error>({
    queryKey: ['pipeline-runs', params],
    queryFn: async (): Promise<PipelineRunSummary[]> => {
      const res = await getPipelineRuns(params);
      return res.data ?? [];
    },
    refetchInterval: 15_000,
  });
}

export function usePipelineGraph(runId: string) {
  return useQuery({
    queryKey: ['pipeline-graph', runId],
    queryFn: async () => {
      const res = await getPipelineGraph(runId);
      if (!res.data) throw new Error('Run graph not found');
      return res.data;
    },
    enabled: !!runId,
  });
}

export function usePipelineLineage() {
  return useQuery<LineageDataset[], Error>({
    queryKey: ['pipeline-lineage'],
    queryFn: async (): Promise<LineageDataset[]> => {
      const res = await getPipelineLineage();
      return res.data ?? [];
    },
  });
}
