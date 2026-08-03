/**
 * QuickActions.tsx — 7 navigation shortcut cards covering all platform modules.
 */

import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FlaskConical,
  Play,
  Brain,
  BarChart3,
  Archive,
  GitBranch,
  ChevronRight,
} from 'lucide-react';
import { Zap } from 'lucide-react';

interface ActionCard {
  label: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  accent: string;
  iconBg: string;
}

const ACTIONS: ActionCard[] = [
  {
    label: 'Upload Dataset',
    description: 'Add a new CSV dataset to the registry',
    icon: <Upload size={20} />,
    path: '/datasets',
    accent: 'var(--color-accent-blue)',
    iconBg: 'rgba(59,130,246,0.12)',
  },
  {
    label: 'Create Experiment',
    description: 'Define a new ML experiment',
    icon: <FlaskConical size={20} />,
    path: '/experiments',
    accent: 'var(--color-accent-purple)',
    iconBg: 'rgba(139,92,246,0.12)',
  },
  {
    label: 'Execute Run',
    description: 'Train a model on an existing experiment',
    icon: <Play size={20} />,
    path: '/experiments',
    accent: 'var(--color-accent-cyan)',
    iconBg: 'rgba(6,182,212,0.12)',
  },
  {
    label: 'Training Ops',
    description: 'Monitor training executions and queues',
    icon: <Brain size={20} />,
    path: '/training',
    accent: 'var(--color-accent-emerald)',
    iconBg: 'rgba(16,185,129,0.12)',
  },
  {
    label: 'Metrics Dashboard',
    description: 'Analyse performance across experiments',
    icon: <BarChart3 size={20} />,
    path: '/metrics',
    accent: 'var(--color-accent-blue)',
    iconBg: 'rgba(59,130,246,0.12)',
  },
  {
    label: 'Artifact Registry',
    description: 'Browse generated models and files',
    icon: <Archive size={20} />,
    path: '/artifacts',
    accent: 'var(--color-accent-purple)',
    iconBg: 'rgba(139,92,246,0.12)',
  },
  {
    label: 'Pipeline Viewer',
    description: 'Visualise the end-to-end ML workflow',
    icon: <GitBranch size={20} />,
    path: '/pipeline',
    accent: 'var(--color-accent-cyan)',
    iconBg: 'rgba(6,182,212,0.12)',
  },
];

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <div className="card p-5">
      <h3 className="section-title mb-1 flex items-center gap-2">
        <Zap size={16} className="text-accent-cyan" />
        Quick Actions
      </h3>
      <p className="text-xs text-muted-foreground mb-4">Navigate directly to any platform module</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-2">
        {ACTIONS.map(action => (
          <button
            key={action.label}
            onClick={() => navigate(action.path)}
            className="flex items-center gap-3 p-3 rounded-lg text-left transition-all duration-150 hover:scale-[1.01]"
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = action.accent;
              (e.currentTarget as HTMLButtonElement).style.boxShadow = `0 0 12px ${action.iconBg}`;
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-border)';
              (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
            }}
          >
            <div
              className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: action.iconBg, color: action.accent }}
            >
              {action.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{action.label}</p>
              <p className="text-xs text-muted-foreground truncate">{action.description}</p>
            </div>
            <ChevronRight size={14} className="text-muted-foreground flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}
