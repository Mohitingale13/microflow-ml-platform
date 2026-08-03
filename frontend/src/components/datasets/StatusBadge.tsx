import { cn } from '../../utils/cn';
import type { DatasetListItem } from '../../types/dataset.types';

interface StatusBadgeProps {
  status: DatasetListItem['status'];
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variants = {
    uploaded: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    analysing: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    ready: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    error: 'bg-red-500/20 text-red-400 border border-red-500/30',
  };

  const labels = {
    uploaded: 'Uploaded',
    analysing: 'Analysing',
    ready: 'Ready',
    error: 'Error',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        variants[status]
      )}
    >
      {labels[status]}
    </span>
  );
}
