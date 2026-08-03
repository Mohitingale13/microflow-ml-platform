/**
 * BestPerformingAssets.tsx — Highlight cards for the top-performing entities.
 */

import { useNavigate } from 'react-router-dom';
import { Trophy, FlaskConical, Database, Archive, Award } from 'lucide-react';
import type { QuickStats } from '@/types/dashboard.types';
import { formatRelativeTime } from '@/utils/time';

interface BestPerformingAssetsProps {
  stats: QuickStats | undefined;
  isLoading: boolean;
}

function AssetCard({
  title,
  icon,
  accent,
  iconBg,
  children,
  onClick,
}: {
  title: string;
  icon: React.ReactNode;
  accent: string;
  iconBg: string;
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <div
      className={`card p-4 flex flex-col gap-3 ${onClick ? 'cursor-pointer hover:scale-[1.01] transition-transform' : ''}`}
      style={{ borderColor: 'var(--color-border)' }}
      onClick={onClick}
      onMouseEnter={e => onClick && ((e.currentTarget as HTMLDivElement).style.borderColor = accent)}
      onMouseLeave={e => onClick && ((e.currentTarget as HTMLDivElement).style.borderColor = 'var(--color-border)')}
    >
      <div className="flex items-center gap-2">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: iconBg, color: accent }}
        >
          {icon}
        </div>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{title}</span>
      </div>
      {children}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="card p-4 animate-pulse space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-surface-2" />
        <div className="h-3 bg-surface-2 rounded w-20" />
      </div>
      <div className="h-5 bg-surface-2 rounded w-36" />
      <div className="h-3 bg-surface-2 rounded w-28" />
    </div>
  );
}

function NullCard({ title, icon, accent, iconBg, message }: {
  title: string; icon: React.ReactNode; accent: string; iconBg: string; message: string;
}) {
  return (
    <AssetCard title={title} icon={icon} accent={accent} iconBg={iconBg}>
      <p className="text-sm text-muted-foreground">{message}</p>
    </AssetCard>
  );
}

export function BestPerformingAssets({ stats, isLoading }: BestPerformingAssetsProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div>
        <h3 className="section-title mb-1 flex items-center gap-2">
          <Award size={16} className="text-accent-cyan" />
          Best Performing Assets
        </h3>
        <p className="text-xs text-muted-foreground mb-4">Top entities across the platform</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (!stats) return null;

  // Friendly model label
  const modelLabel = stats.best_model_type
    ? stats.best_model_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : null;

  return (
    <div>
      <h3 className="section-title mb-1 flex items-center gap-2">
        <Award size={16} className="text-accent-cyan" />
        Best Performing Assets
      </h3>
      <p className="text-xs text-muted-foreground mb-4">Top entities across the platform</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Best Model */}
        {modelLabel ? (
          <AssetCard
            title="Best Model"
            icon={<Trophy size={16} />}
            accent="var(--color-accent-emerald)"
            iconBg="rgba(16,185,129,0.12)"
          >
            <p className="text-base font-semibold text-text-primary">{modelLabel}</p>
            <div className="space-y-0.5">
              {stats.best_model_accuracy != null && (
                <p className="text-xs text-muted-foreground">
                  Avg accuracy: <span className="text-emerald-400 font-medium">{(stats.best_model_accuracy * 100).toFixed(2)}%</span>
                </p>
              )}
              {stats.best_model_run_count != null && (
                <p className="text-xs text-muted-foreground">{stats.best_model_run_count} run{stats.best_model_run_count === 1 ? '' : 's'}</p>
              )}
            </div>
          </AssetCard>
        ) : (
          <NullCard title="Best Model" icon={<Trophy size={16} />} accent="var(--color-accent-emerald)" iconBg="rgba(16,185,129,0.12)" message="No completed runs yet" />
        )}

        {/* Best Experiment */}
        {stats.best_experiment_id ? (
          <AssetCard
            title="Best Experiment"
            icon={<FlaskConical size={16} />}
            accent="var(--color-accent-purple)"
            iconBg="rgba(139,92,246,0.12)"
            onClick={() => navigate(`/experiments/${stats.best_experiment_id}`)}
          >
            <p className="text-base font-semibold text-text-primary truncate">{stats.best_experiment_name}</p>
            <div className="space-y-0.5">
              {stats.best_experiment_accuracy != null && (
                <p className="text-xs text-muted-foreground">
                  Best accuracy: <span className="text-purple-400 font-medium">{(stats.best_experiment_accuracy * 100).toFixed(2)}%</span>
                </p>
              )}
              {stats.best_experiment_run_count != null && (
                <p className="text-xs text-muted-foreground">{stats.best_experiment_run_count} run{stats.best_experiment_run_count === 1 ? '' : 's'}</p>
              )}
            </div>
          </AssetCard>
        ) : (
          <NullCard title="Best Experiment" icon={<FlaskConical size={16} />} accent="var(--color-accent-purple)" iconBg="rgba(139,92,246,0.12)" message="No experiments yet" />
        )}

        {/* Most Used Dataset */}
        {stats.most_used_dataset_id ? (
          <AssetCard
            title="Most Used Dataset"
            icon={<Database size={16} />}
            accent="var(--color-accent-blue)"
            iconBg="rgba(59,130,246,0.12)"
            onClick={() => navigate(`/datasets/${stats.most_used_dataset_id}`)}
          >
            <p className="text-base font-semibold text-text-primary truncate">{stats.most_used_dataset_name}</p>
            <div className="space-y-0.5">
              {stats.most_used_dataset_experiment_count != null && (
                <p className="text-xs text-muted-foreground">
                  <span className="text-blue-400 font-medium">{stats.most_used_dataset_experiment_count}</span> experiment{stats.most_used_dataset_experiment_count === 1 ? '' : 's'}
                </p>
              )}
            </div>
          </AssetCard>
        ) : (
          <NullCard title="Most Used Dataset" icon={<Database size={16} />} accent="var(--color-accent-blue)" iconBg="rgba(59,130,246,0.12)" message="No datasets uploaded" />
        )}

        {/* Most Recent Artifact */}
        {stats.latest_artifact_id ? (
          <AssetCard
            title="Latest Artifact"
            icon={<Archive size={16} />}
            accent="var(--color-accent-cyan)"
            iconBg="rgba(6,182,212,0.12)"
            onClick={() => navigate('/artifacts')}
          >
            <p className="text-base font-semibold text-text-primary truncate">{stats.latest_artifact_filename}</p>
            <div className="space-y-0.5">
              {stats.latest_artifact_type && (
                <p className="text-xs text-muted-foreground capitalize">
                  {stats.latest_artifact_type.replace(/_/g, ' ')}
                </p>
              )}
              {stats.latest_artifact_created_at && (
                <p className="text-xs text-muted-foreground">
                  {formatRelativeTime(stats.latest_artifact_created_at)}
                </p>
              )}
            </div>
          </AssetCard>
        ) : (
          <NullCard title="Latest Artifact" icon={<Archive size={16} />} accent="var(--color-accent-cyan)" iconBg="rgba(6,182,212,0.12)" message="No artifacts yet" />
        )}
      </div>
    </div>
  );
}
