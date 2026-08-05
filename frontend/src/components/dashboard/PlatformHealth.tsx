/**
 * PlatformHealth.tsx — Backend health status section.
 * Reuses the existing useHealth() hook.
 */

import { useState } from 'react';
import { CheckCircle2, XCircle, AlertCircle, RefreshCw, Server, Database, Wifi, HardDrive } from 'lucide-react';
import { useHealth } from '@/hooks/useHealth';

interface StatusRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  statusClass?: string;
}

function StatusRow({ icon, label, value, statusClass }: StatusRowProps) {
  return (
    <div className="backend-status-item">
      <span className="backend-status-key flex items-center gap-1.5">
        <span className="opacity-60">{icon}</span>
        {label}
      </span>
      <span className={`backend-status-val ${statusClass ?? ''}`}>{value}</span>
    </div>
  );
}

function StatusIndicator({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: 'var(--color-accent-emerald)' }}>
      <CheckCircle2 size={14} />
      Operational
    </span>
  ) : (
    <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: 'var(--color-accent-red)' }}>
      <XCircle size={14} />
      Unavailable
    </span>
  );
}

export function PlatformHealth() {
  const { data: health, isLoading, isError, refetch, isRefetching } = useHealth();
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [refreshSuccess, setRefreshSuccess] = useState(false);

  async function handleRefresh() {
    setIsManualRefreshing(true);
    const start = Date.now();
    try {
      await refetch();
      const elapsed = Date.now() - start;
      if (elapsed < 500) await new Promise(r => setTimeout(r, 500 - elapsed));
    } finally {
      setIsManualRefreshing(false);
      setRefreshSuccess(true);
      setTimeout(() => setRefreshSuccess(false), 2000);
    }
  }

  const isHealthy = !!health && !isError;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title mb-0 flex items-center gap-2">
          <Server size={16} className="text-accent-cyan" />
          Platform Health
        </h3>
        <div className="flex items-center gap-3">
          <StatusIndicator ok={isHealthy} />
          <button
            onClick={handleRefresh}
            disabled={isRefetching || isManualRefreshing}
            className="px-3.5 py-1.5 text-xs font-bold text-gray-200 hover:text-white border border-white/15 rounded-xl bg-white/5 hover:bg-white/10 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer disabled:opacity-50"
          >
            {refreshSuccess ? (
              <>
                <CheckCircle2 size={13} className="text-emerald-400" />
                <span className="text-emerald-300 font-bold">Checked!</span>
              </>
            ) : (
              <>
                <RefreshCw size={12} className={isRefetching || isManualRefreshing ? 'animate-spin text-purple-300' : ''} />
                <span>{isRefetching || isManualRefreshing ? 'Checking...' : 'Refresh'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="animate-pulse space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 bg-surface-2 rounded" />
          ))}
        </div>
      )}

      {isError && (
        <div className="flex items-center gap-2 p-3 rounded-lg text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--color-accent-red)' }}>
          <AlertCircle size={16} />
          Unable to reach backend. Ensure the server is running.
        </div>
      )}

      {health && (
        <div className="backend-status-grid">
          <StatusRow icon={<Server size={13} />} label="Service" value={health.service} />
          <StatusRow icon={<Wifi size={13} />} label="Status" value={health.status} statusClass="backend-status-val--healthy" />
          <StatusRow icon={<Database size={13} />} label="Environment" value={health.environment} />
          <StatusRow icon={<HardDrive size={13} />} label="Version" value={health.version} />
          <StatusRow
            icon={<RefreshCw size={13} />}
            label="Last Check"
            value={new Date(health.timestamp).toLocaleTimeString()}
          />
        </div>
      )}
    </div>
  );
}
