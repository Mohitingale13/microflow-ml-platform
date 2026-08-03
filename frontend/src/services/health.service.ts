import { get } from "@/services/api";
import type { ApiResponse, HealthData } from "@/types/api.types";

export async function getHealth(): Promise<ApiResponse<HealthData>> {
  return get<HealthData>("/health");
}
