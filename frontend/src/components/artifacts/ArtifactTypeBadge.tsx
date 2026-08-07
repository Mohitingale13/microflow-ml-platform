import { FileCode, Cpu, BarChart2, CheckCircle, Sliders, Table, Activity, Eye, FileJson } from 'lucide-react';
import type { ArtifactType } from '@/types/artifact.types';

interface ArtifactTypeBadgeProps {
  type: ArtifactType | string;
  size?: 'sm' | 'md';
}

const TYPE_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  trained_model: {
    label: 'Trained Model',
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/20',
    icon: Cpu,
  },
  metrics_json: {
    label: 'Metrics',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    icon: BarChart2,
  },
  evaluation_json: {
    label: 'Evaluation',
    bg: 'bg-cyan-500/10',
    text: 'text-cyan-400',
    border: 'border-cyan-500/20',
    icon: CheckCircle,
  },
  confusion_matrix_json: {
    label: 'Confusion Matrix',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    icon: Table,
  },
  configuration_json: {
    label: 'Configuration',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
    icon: Sliders,
  },
  preprocessing_json: {
    label: 'Preprocessing',
    bg: 'bg-indigo-500/10',
    text: 'text-indigo-400',
    border: 'border-indigo-500/20',
    icon: FileCode,
  },
  shap_summary_png: {
    label: 'SHAP Summary',
    bg: 'bg-fuchsia-500/10',
    text: 'text-fuchsia-400',
    border: 'border-fuchsia-500/20',
    icon: Eye,
  },
  feature_importance_png: {
    label: 'Feature Importance Plot',
    bg: 'bg-pink-500/10',
    text: 'text-pink-400',
    border: 'border-pink-500/20',
    icon: BarChart2,
  },
  shap_dependence_png: {
    label: 'SHAP Dependence',
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/20',
    icon: Activity,
  },
  shap_values_json: {
    label: 'SHAP Values',
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/20',
    icon: FileJson,
  },
  feature_importance_json: {
    label: 'Feature Importance JSON',
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/20',
    icon: FileJson,
  },
  explainability_summary_json: {
    label: 'Explainability Summary',
    bg: 'bg-violet-500/10',
    text: 'text-violet-400',
    border: 'border-violet-500/20',
    icon: Eye,
  },
};

export function ArtifactTypeBadge({ type, size = 'md' }: ArtifactTypeBadgeProps) {
  const config = TYPE_CONFIG[type] || {
    label: type,
    bg: 'bg-gray-500/10',
    text: 'text-gray-400',
    border: 'border-gray-500/20',
    icon: FileCode,
  };

  const Icon = config.icon;
  const isSm = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border rounded-md ${config.bg} ${config.text} ${config.border} ${
        isSm ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
      }`}
    >
      <Icon className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
}
