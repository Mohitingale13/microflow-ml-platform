import api from './api';
import type { ApiResponse } from '../types/api.types';
import type {
  Dataset,
  DatasetListItem,
  DatasetPreview,
  DatasetStatistics,
} from '../types/dataset.types';

export const getDatasets = async (): Promise<ApiResponse<DatasetListItem[]>> => {
  const response = await api.get<ApiResponse<DatasetListItem[]>>('/datasets');
  return response.data;
};

export const getDataset = async (id: string): Promise<ApiResponse<Dataset>> => {
  const response = await api.get<ApiResponse<Dataset>>(`/datasets/${id}`);
  return response.data;
};

export const uploadDataset = async (formData: FormData): Promise<ApiResponse<Dataset>> => {
  const response = await api.post<ApiResponse<Dataset>>('/datasets', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDatasetPreview = async (id: string): Promise<ApiResponse<DatasetPreview>> => {
  const response = await api.get<ApiResponse<DatasetPreview>>(`/datasets/${id}/preview`);
  return response.data;
};

export const getDatasetStatistics = async (id: string): Promise<ApiResponse<DatasetStatistics>> => {
  const response = await api.get<ApiResponse<DatasetStatistics>>(`/datasets/${id}/statistics`);
  return response.data;
};

export const deleteDataset = async (id: string): Promise<ApiResponse<null>> => {
  const response = await api.delete<ApiResponse<null>>(`/datasets/${id}`);
  return response.data;
};
