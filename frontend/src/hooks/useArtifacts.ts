import { useQuery } from '@tanstack/react-query';
import {
  getArtifacts,
  getArtifactStats,
  getArtifact,
} from '@/services/artifact.service';

export function useArtifacts() {
  return useQuery({
    queryKey: ['artifacts'],
    queryFn: async () => {
      const response = await getArtifacts();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch artifacts');
      }
      return response.data ?? [];
    },
  });
}

export function useArtifactStats() {
  return useQuery({
    queryKey: ['artifacts-stats'],
    queryFn: async () => {
      const response = await getArtifactStats();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch artifact stats');
      }
      return response.data;
    },
  });
}

export function useArtifact(id: string) {
  return useQuery({
    queryKey: ['artifact', id],
    queryFn: async () => {
      const response = await getArtifact(id);
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch artifact details');
      }
      return response.data;
    },
    enabled: !!id,
  });
}
