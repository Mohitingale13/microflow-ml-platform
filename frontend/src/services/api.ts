import axios from "axios";
import type { ApiResponse } from "@/types/api.types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10_000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = "An unexpected error occurred";
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail) && data.detail.length > 0) {
        message = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
      } else if (typeof data.message === "string") {
        message = data.message;
      } else if (typeof data.error === "string") {
        message = data.error;
      }
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

export async function get<T>(url: string): Promise<ApiResponse<T>> {
  const response = await apiClient.get<ApiResponse<T>>(url);
  return response.data;
}

export async function post<T, B = unknown>(url: string, body: B): Promise<ApiResponse<T>> {
  const response = await apiClient.post<ApiResponse<T>>(url, body);
  return response.data;
}

export default apiClient;
