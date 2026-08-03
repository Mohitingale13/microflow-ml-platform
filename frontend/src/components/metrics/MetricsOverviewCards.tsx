/**
 * MetricsOverviewCards.tsx — Overview summary metric cards for the Metrics Dashboard.
 */

import {
  Activity,
  Award,
  CheckCircle2,
  Clock,
  Layers,
  Percent,
  TrendingUp,
} from 'lucide-react';
import type { MetricsOverview } from '@/types/metrics.types';

interface MetricsOverviewCardsProps {
  overview?: MetricsOverview;
  isLoading: boolean;
}

export function MetricsOverviewCards({ overview, isLoading }: MetricsOverviewCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="card p-4 animate-pulse">
            <div className="h-4 bg-muted/60 rounded w-1/2 mb-3"></div>
            <div className="h-7 bg-muted rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Runs',
      value: overview ? overview.total_runs.toLocaleString() : '0',
      subValue: overview ? `${overview.failed_runs} failed` : '',
      icon: <Layers size={18} className="text-primary" />,
      color: 'text-foreground',
    },
    {
      label: 'Completed Runs',
      value: overview ? overview.completed_runs.toLocaleString() : '0',
      subValue: 'Persisted results',
      icon: <CheckCircle2 size={18} className="text-emerald-400" />,
      color: 'text-emerald-400',
    },
    {
      label: 'Success Rate',
      value: overview ? `${(overview.success_rate * 100).toFixed(1)}%` : '0.0%',
      subValue: 'All executions',
      icon: <Percent size={18} className="text-blue-400" />,
      color: 'text-blue-400',
    },
    {
      label: 'Avg Accuracy',
      value:
        overview?.average_accuracy !== null && overview?.average_accuracy !== undefined
          ? `${(overview.average_accuracy * 100).toFixed(2)}%`
          : '—',
      subValue: 'Across completed',
      icon: <Award size={18} className="text-amber-400" />,
      color: 'text-amber-400',
    },
    {
      label: 'Avg F1 Score',
      value:
        overview?.average_f1 !== null && overview?.average_f1 !== undefined
          ? `${(overview.average_f1 * 100).toFixed(2)}%`
          : '—',
      subValue: 'Harmonic mean',
      icon: <TrendingUp size={18} className="text-purple-400" />,
      color: 'text-purple-400',
    },
    {
      label: 'Avg ROC AUC',
      value:
        overview?.average_roc_auc !== null && overview?.average_roc_auc !== undefined
          ? overview.average_roc_auc.toFixed(4)
          : '—',
      subValue: 'Classification power',
      icon: <Activity size={18} className="text-cyan-400" />,
      color: 'text-cyan-400',
    },
    {
      label: 'Avg Duration',
      value:
        overview?.average_training_duration !== null &&
        overview?.average_training_duration !== undefined
          ? `${overview.average_training_duration.toFixed(2)}s`
          : '—',
      subValue: 'Per run execution',
      icon: <Clock size={18} className="text-pink-400" />,
      color: 'text-pink-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
      {cards.map((card, idx) => (
        <div key={idx} className="card p-4 flex flex-col justify-between hover:border-primary/40 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">{card.label}</span>
            {card.icon}
          </div>
          <div>
            <div className={`text-xl font-bold font-mono ${card.color}`}>{card.value}</div>
            <div className="text-[11px] text-muted-foreground mt-1 truncate">{card.subValue}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
