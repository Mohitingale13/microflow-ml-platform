/**
 * dashboard.types.ts — TypeScript interfaces for the Dashboard API.
 */

// ── Overview ──────────────────────────────────────────────────────────────────

export interface DashboardOverview {
  total_datasets: number;
  total_experiments: number;
  total_runs: number;
  completed_runs: number;
  running_runs: number;
  failed_runs: number;
  total_artifacts: number;
  models_stored: number;
  success_rate: number;
  average_accuracy: number | null;
  average_f1: number | null;
  average_roc_auc: number | null;
  average_training_duration_seconds: number | null;
  storage_used_bytes: number;
}

// ── Activity Feed ─────────────────────────────────────────────────────────────

export type ActivityEventType =
  | 'dataset_uploaded'
  | 'experiment_created'
  | 'run_created'
  | 'run_queued'
  | 'run_completed'
  | 'run_failed'
  | 'artifact_generated'
  | 'metrics_persisted';

export interface ActivityItem {
  event_type: ActivityEventType;
  entity_type: 'dataset' | 'experiment' | 'run' | 'artifact' | 'result';
  entity_id: string;
  entity_name: string;
  description: string;
  occurred_at: string;  // ISO 8601
  metadata: Record<string, unknown> | null;
}

// ── Recent Runs ───────────────────────────────────────────────────────────────

export interface RecentRunItem {
  run_id: string;
  run_number: number;
  experiment_id: string;
  experiment_name: string;
  dataset_id: string | null;
  dataset_name: string | null;
  model: string | null;
  status: string;
  accuracy: number | null;
  duration_seconds: number | null;
  started_at: string | null;
  completed_at: string | null;
  artifact_count: number;
}

// ── Quick Stats ───────────────────────────────────────────────────────────────

export interface QuickStats {
  best_model_type: string | null;
  best_model_accuracy: number | null;
  best_model_run_count: number | null;
  best_experiment_id: string | null;
  best_experiment_name: string | null;
  best_experiment_accuracy: number | null;
  best_experiment_run_count: number | null;
  most_used_dataset_id: string | null;
  most_used_dataset_name: string | null;
  most_used_dataset_experiment_count: number | null;
  latest_artifact_id: string | null;
  latest_artifact_filename: string | null;
  latest_artifact_type: string | null;
  latest_artifact_run_id: string | null;
  latest_artifact_created_at: string | null;
}
