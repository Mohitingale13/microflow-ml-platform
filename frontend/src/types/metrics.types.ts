/**
 * metrics.types.ts — TypeScript interface definitions for the Metrics Dashboard.
 */

export interface MetricsOverview {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  success_rate: number;
  average_accuracy: number | null;
  average_precision: number | null;
  average_recall: number | null;
  average_f1: number | null;
  average_roc_auc: number | null;
  average_training_duration: number | null;
}

export interface ModelMetricSummary {
  model_type: string;
  number_of_runs: number;
  best_accuracy: number | null;
  average_accuracy: number | null;
  best_f1: number | null;
  average_f1: number | null;
  average_roc_auc: number | null;
  average_duration: number | null;
}

export interface ExperimentMetricSummary {
  experiment_id: string;
  experiment_name: string;
  dataset_id: string | null;
  dataset_name: string | null;
  total_runs: number;
  best_run_id: string | null;
  best_run_number: number | null;
  best_accuracy: number | null;
  average_accuracy: number | null;
  latest_run_id: string | null;
  latest_run_number: number | null;
  latest_run_status: string | null;
  latest_run_created_at: string | null;
}

export interface DatasetMetricSummary {
  dataset_id: string;
  dataset_name: string;
  number_of_experiments: number;
  number_of_runs: number;
  best_model: string | null;
  best_accuracy: number | null;
}

export interface RunComparisonItem {
  run_id: string;
  run_number: number;
  experiment_id: string;
  experiment_name: string;
  dataset_id: string | null;
  dataset_name: string | null;
  model: string | null;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  roc_auc: number | null;
  duration: number | null;
  training_configuration: Record<string, any> | null;
  completed_at: string | null;
}

export interface MetricsFilterState {
  dataset_id?: string;
  experiment_id?: string;
  model_type?: string;
  search_term?: string;
}
