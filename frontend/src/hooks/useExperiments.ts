import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  cancelRun,
  createExperiment,
  createRun,
  deleteExperiment,
  getExperiment,
  getExperimentRuns,
  getExperiments,
  getRun,
  getRuns,
  getRunArtifacts,
  getRunResult,
  queueRun,
  updateExperiment,
  updateRun,
  deleteRun,
  executeRun,
} from '../services/experiment.service';
import type {
  ExperimentCreate,
  ExperimentUpdate,
  RunCreate,
  RunUpdate,
  ExecuteRunRequest,
} from '../types/experiment.types';

// ─── Experiment Hooks ──────────────────────────────────────────────────────────

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: async () => {
      const response = await getExperiments();
      if (!response.success) throw new Error(response.message);
      return response.data ?? [];
    },
  });
}

export function useExperiment(id: string) {
  return useQuery({
    queryKey: ['experiment', id],
    queryFn: async () => {
      const response = await getExperiment(id);
      if (!response.success) throw new Error(response.message);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExperimentCreate) => createExperiment(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
    },
  });
}

export function useUpdateExperiment(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExperimentUpdate) => updateExperiment(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      queryClient.invalidateQueries({ queryKey: ['experiment', id] });
    },
  });
}

export function useDeleteExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteExperiment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
    },
  });
}

// ─── Run Hooks ─────────────────────────────────────────────────────────────────

export function useRuns() {
  return useQuery({
    queryKey: ['runs'],
    queryFn: async () => {
      const response = await getRuns();
      if (!response.success) throw new Error(response.message);
      return response.data ?? [];
    },
  });
}

export function useExperimentRuns(experimentId: string) {
  return useQuery({
    queryKey: ['runs', experimentId],
    queryFn: async () => {
      const response = await getExperimentRuns(experimentId);
      if (!response.success) throw new Error(response.message);
      return response.data ?? [];
    },
    enabled: !!experimentId,
  });
}

export function useRun(id: string) {
  return useQuery({
    queryKey: ['run', id],
    queryFn: async () => {
      const response = await getRun(id);
      if (!response.success) throw new Error(response.message);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RunCreate) => createRun(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['runs', variables.experiment_id] });
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });
}

export function useUpdateRun(id: string, experimentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RunUpdate) => updateRun(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['run', id] });
      queryClient.invalidateQueries({ queryKey: ['runs', experimentId] });
    },
  });
}

export function useQueueRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string; experimentId: string }) => queueRun(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['run', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['runs', variables.experimentId] });
    },
  });
}

export function useCancelRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string; experimentId: string }) => cancelRun(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['run', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['runs', variables.experimentId] });
    },
  });
}

export function useDeleteRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteRun(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });
}

export function useExecuteRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      experimentId: string;
      payload: ExecuteRunRequest;
    }) => executeRun(id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['run', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['runs', variables.experimentId] });
      queryClient.invalidateQueries({ queryKey: ['runs'] });
      // Invalidate results and artifacts so they reload after execution
      queryClient.invalidateQueries({ queryKey: ['run-result', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['run-artifacts', variables.id] });
    },
  });
}

export function useRunResult(runId: string) {
  return useQuery({
    queryKey: ['run-result', runId],
    queryFn: async () => {
      const response = await getRunResult(runId);
      if (!response.success) throw new Error(response.message);
      return response.data ?? null;
    },
    enabled: !!runId,
  });
}

export function useRunArtifacts(runId: string) {
  return useQuery({
    queryKey: ['run-artifacts', runId],
    queryFn: async () => {
      const response = await getRunArtifacts(runId);
      if (!response.success) throw new Error(response.message);
      return response.data ?? [];
    },
    enabled: !!runId,
  });
}
