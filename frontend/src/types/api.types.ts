export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  errors: string[] | null;
}

export interface HealthData {
  service: string;
  version: string;
  status: string;
  environment: string;
  timestamp: string;
}
