/**
 * useDashboard.ts — TanStack Query hooks for the Dashboard.
 */

import { useQuery } from '@tanstack/react-query';
import {
  getDashboardActivity,
  getDashboardOverview,
  getDashboardQuickStats,
  getDashboardRecentRuns,
} from '@/services/dashboard.service';
import type {
  ActivityItem,
  DashboardOverview,
  QuickStats,
  RecentRunItem,
} from '@/types/dashboard.types';

// ─── Hooks ────────────────────────────────────────────────────────────────────

export function useDashboardOverview() {
  return useQuery<DashboardOverview, Error>({
    queryKey: ['dashboard-overview'],
    queryFn: async (): Promise<DashboardOverview> => {
      const res = await getDashboardOverview();
      if (!res.data) throw new Error(res.message || 'Failed to fetch overview');
      return res.data;
    },
    refetchInterval: 30_000, // auto-refresh every 30s
  });
}

export function useDashboardActivity(limit = 20) {
  return useQuery<ActivityItem[], Error>({
    queryKey: ['dashboard-activity', limit],
    queryFn: async (): Promise<ActivityItem[]> => {
      const res = await getDashboardActivity(limit);
      return res.data ?? [];
    },
    refetchInterval: 30_000,
  });
}

export function useDashboardRecentRuns(limit = 10) {
  return useQuery<RecentRunItem[], Error>({
    queryKey: ['dashboard-recent-runs', limit],
    queryFn: async (): Promise<RecentRunItem[]> => {
      const res = await getDashboardRecentRuns(limit);
      return res.data ?? [];
    },
    refetchInterval: 30_000,
  });
}

export function useDashboardQuickStats() {
  return useQuery<QuickStats, Error>({
    queryKey: ['dashboard-quick-stats'],
    queryFn: async (): Promise<QuickStats> => {
      const res = await getDashboardQuickStats();
      if (!res.data) throw new Error(res.message || 'Failed to fetch quick stats');
      return res.data;
    },
    refetchInterval: 60_000, // refresh every minute — changes less frequently
  });
}
