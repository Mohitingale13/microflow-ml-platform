import { get } from './api';
import type { ApiResponse } from '@/types/api.types';
import type {
  Artifact,
  ArtifactDetail,
  ArtifactRegistryStats,
} from '@/types/artifact.types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function getArtifacts(): Promise<ApiResponse<Artifact[]>> {
  return get<Artifact[]>('/artifacts');
}

export async function getArtifactStats(): Promise<ApiResponse<ArtifactRegistryStats>> {
  return get<ArtifactRegistryStats>('/artifacts/stats');
}

export async function getArtifact(id: string): Promise<ApiResponse<ArtifactDetail>> {
  return get<ArtifactDetail>(`/artifacts/${id}`);
}

/**
 * Returns the direct download URL for an artifact.
 * Opened via window.open or an <a> tag.
 */
export function getArtifactDownloadUrl(id: string): string {
  return `${BASE_URL}/api/v1/artifacts/${id}/download`;
}
