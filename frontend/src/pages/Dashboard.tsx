/**
 * Dashboard.tsx — Production-quality engineering command centre for MicroFlow.
 *
 * Sections:
 *   1. Platform Overview   — 8 stat cards
 *   2. Platform Health     — backend health status
 *   3. Recent Activity     — timestamped activity feed
 *   4. Quick Actions       — 7 navigation shortcuts
 *   5. Recent Runs         — last 10 runs table
 *   6. Platform Analytics  — compact charts
 *   7. Best Performing     — best model / experiment / dataset / artifact
 */

import { RefreshCw, LayoutDashboard } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { OverviewCards } from '@/components/dashboard/OverviewCards';
import { PlatformHealth } from '@/components/dashboard/PlatformHealth';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { RecentRunsTable } from '@/components/dashboard/RecentRunsTable';
import { MiniCharts } from '@/components/dashboard/MiniCharts';
import { BestPerformingAssets } from '@/components/dashboard/BestPerformingAssets';

import {
  useDashboardOverview,
  useDashboardActivity,
  useDashboardRecentRuns,
  useDashboardQuickStats,
} from '@/hooks/useDashboard';
import { useModelMetrics } from '@/hooks/useMetrics';

export function Dashboard() {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: overview, isLoading: overviewLoading } = useDashboardOverview();
  const { data: activity = [], isLoading: activityLoading } = useDashboardActivity(5);
  const { data: recentRuns = [], isLoading: runsLoading } = useDashboardRecentRuns(5);
  const { data: quickStats, isLoading: statsLoading } = useDashboardQuickStats();
  const { data: modelMetrics = [], isLoading: chartsLoading } = useModelMetrics();

  async function handleRefreshAll() {
    setIsRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
    await queryClient.invalidateQueries({ queryKey: ['dashboard-activity'] });
    await queryClient.invalidateQueries({ queryKey: ['dashboard-recent-runs'] });
    await queryClient.invalidateQueries({ queryKey: ['dashboard-quick-stats'] });
    await queryClient.invalidateQueries({ queryKey: ['metrics-models'] });
    setTimeout(() => setIsRefreshing(false), 600);
  }

  return (
    <div className="page space-y-6 pb-12">

      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="page-title text-2xl font-bold flex items-center gap-2.5">
            <LayoutDashboard size={24} className="text-primary" />
            ML Operations Dashboard
          </h1>
          <p className="page-subtitle text-xs mt-1">
            Platform-wide overview — datasets, experiments, training runs, artifacts
          </p>
        </div>
        <button
          onClick={handleRefreshAll}
          disabled={isRefreshing}
          className="btn btn-outline text-xs self-start sm:self-auto flex items-center gap-1.5"
        >
          <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
          Refresh All
        </button>
      </div>

      {/* ── Section 1: Platform Overview ─────────────────────────────────── */}
      <OverviewCards overview={overview} isLoading={overviewLoading} />

      {/* ── Sections 2 + 3 (side by side on lg+) ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
        {/* Section 3: Activity Feed */}
        <ActivityFeed events={activity} isLoading={activityLoading} />

        {/* Section 2 + 4: Health + Quick Actions stacked */}
        <div className="space-y-6">
          <PlatformHealth />
          <QuickActions />
        </div>
      </div>

      {/* ── Section 5: Recent Runs ───────────────────────────────────────── */}
      <RecentRunsTable runs={recentRuns} isLoading={runsLoading} />

      {/* ── Section 6: Platform Analytics ───────────────────────────────── */}
      <MiniCharts
        overview={overview}
        modelMetrics={modelMetrics}
        isLoading={overviewLoading || chartsLoading}
      />

      {/* ── Section 7: Best Performing Assets ───────────────────────────── */}
      <BestPerformingAssets stats={quickStats} isLoading={statsLoading} />

    </div>
  );
}
