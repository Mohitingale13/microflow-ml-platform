/**
 * dashboard.service.ts — API client calls for the Dashboard.
 */

import { get } from './api';
import type { ApiResponse } from '@/types/api.types';
import type {
  ActivityItem,
  DashboardOverview,
  QuickStats,
  RecentRunItem,
} from '@/types/dashboard.types';

export async function getDashboardOverview(): Promise<ApiResponse<DashboardOverview>> {
  return get<DashboardOverview>('/dashboard/overview');
}

export async function getDashboardActivity(limit = 20): Promise<ApiResponse<ActivityItem[]>> {
  return get<ActivityItem[]>(`/dashboard/activity?limit=${limit}`);
}

export async function getDashboardRecentRuns(limit = 10): Promise<ApiResponse<RecentRunItem[]>> {
  return get<RecentRunItem[]>(`/dashboard/recent-runs?limit=${limit}`);
}

export async function getDashboardQuickStats(): Promise<ApiResponse<QuickStats>> {
  return get<QuickStats>('/dashboard/quick-stats');
}
