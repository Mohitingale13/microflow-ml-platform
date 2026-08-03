import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  deleteDataset,
  getDataset,
  getDatasetPreview,
  getDatasets,
  getDatasetStatistics,
  uploadDataset,
} from '../services/dataset.service';

export function useDatasets() {
  return useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await getDatasets();
      if (!response.success) {
        throw new Error(response.message);
      }
      return response.data || [];
    },
  });
}

export function useDataset(id: string) {
  return useQuery({
    queryKey: ['dataset', id],
    queryFn: async () => {
      const response = await getDataset(id);
      if (!response.success) {
        throw new Error(response.message);
      }
      return response.data;
    },
    enabled: !!id,
  });
}

export function useDatasetPreview(id: string) {
  return useQuery({
    queryKey: ['dataset-preview', id],
    queryFn: async () => {
      const response = await getDatasetPreview(id);
      if (!response.success) {
        throw new Error(response.message);
      }
      return response.data;
    },
    enabled: !!id,
  });
}

export function useDatasetStatistics(id: string) {
  return useQuery({
    queryKey: ['dataset-statistics', id],
    queryFn: async () => {
      const response = await getDatasetStatistics(id);
      if (!response.success) {
        throw new Error(response.message);
      }
      return response.data;
    },
    enabled: !!id,
  });
}

export function useUploadDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}
