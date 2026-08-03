import { useNavigate } from 'react-router-dom';
import { FlaskConical, Play, Tag } from 'lucide-react';
import { ExperimentStatusBadge } from './RunStatusBadge';
import type { ExperimentListItem } from '@/types/experiment.types';

interface ExperimentTableProps {
  data: ExperimentListItem[];
  runCounts?: Record<string, number>;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export function ExperimentTable({ data, runCounts = {} }: ExperimentTableProps) {
  const navigate = useNavigate();

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-14 h-14 rounded-full bg-surface-2 flex items-center justify-center mb-4">
          <FlaskConical className="w-6 h-6 text-text-muted" />
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-1">No experiments yet</h3>
        <p className="text-sm text-text-muted max-w-xs">
          Create your first experiment to start tracking ML runs.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-2 border-b border-border">
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Name</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden md:table-cell">Status</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden lg:table-cell">Runs</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden xl:table-cell">Tags</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden lg:table-cell">Created</th>
            <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase hidden xl:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((exp) => (
            <tr
              key={exp.id}
              onClick={() => navigate(`/experiments/${exp.id}`)}
              className="hover:bg-surface-2 transition-colors cursor-pointer group"
            >
              <td className="px-4 py-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-md bg-accent-blue/10 flex items-center justify-center shrink-0 mt-0.5">
                    <FlaskConical className="w-4 h-4 text-accent-blue" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-text-primary truncate group-hover:text-accent-blue transition-colors">
                      {exp.name}
                    </p>
                    {exp.description && (
                      <p className="text-xs text-text-muted truncate max-w-xs mt-0.5">
                        {exp.description}
                      </p>
                    )}
                    {exp.objective && (
                      <p className="text-xs text-text-muted/80 italic truncate max-w-xs mt-0.5">
                        {exp.objective}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="px-4 py-4 hidden md:table-cell">
                <ExperimentStatusBadge status={exp.status} />
              </td>
              <td className="px-4 py-4 hidden lg:table-cell">
                <div className="flex items-center gap-1.5 text-sm text-text-secondary">
                  <Play className="w-3.5 h-3.5" />
                  {runCounts[exp.id] ?? '—'}
                </div>
              </td>
              <td className="px-4 py-4 hidden xl:table-cell">
                {exp.tags && exp.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {exp.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 text-[10px] font-medium text-text-muted bg-surface-2 border border-border rounded-full px-2 py-0.5"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        {tag}
                      </span>
                    ))}
                    {exp.tags.length > 3 && (
                      <span className="text-[10px] text-text-muted">+{exp.tags.length - 3}</span>
                    )}
                  </div>
                ) : (
                  <span className="text-xs text-text-muted">—</span>
                )}
              </td>
              <td className="px-4 py-4 hidden lg:table-cell">
                <span className="text-xs text-text-muted">{formatDate(exp.created_at)}</span>
              </td>
              <td className="px-4 py-4 hidden xl:table-cell">
                <span className="text-xs text-text-muted">{formatDate(exp.updated_at)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
