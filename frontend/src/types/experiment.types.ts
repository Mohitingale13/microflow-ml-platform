// ─── Experiment Types ──────────────────────────────────────────────────────────

export type ExperimentStatus = 'draft' | 'active' | 'archived';

export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  dataset_id: string;
  objective: string | null;
  default_configuration: Record<string, unknown> | null;
  tags: string[] | null;
  status: ExperimentStatus;
  created_at: string;
  updated_at: string;
}

export interface ExperimentListItem {
  id: string;
  name: string;
  description: string | null;
  dataset_id: string;
  objective: string | null;
  tags: string[] | null;
  status: ExperimentStatus;
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  name: string;
  dataset_id: string;
  description?: string | null;
  objective?: string | null;
  default_configuration?: Record<string, unknown> | null;
  tags?: string[] | null;
}

export interface ExperimentUpdate {
  name?: string;
  description?: string | null;
  objective?: string | null;
  default_configuration?: Record<string, unknown> | null;
  tags?: string[] | null;
  status?: ExperimentStatus;
}

// ─── Run Types ─────────────────────────────────────────────────────────────────

export type RunStatus = 'draft' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Run {
  id: string;
  experiment_id: string;
  run_number: number;
  model_type: string | null;
  training_configuration: Record<string, unknown> | null;
  notes: string | null;
  status: RunStatus;
  created_at: string;
  updated_at: string;
}

export interface RunListItem {
  id: string;
  experiment_id: string;
  run_number: number;
  model_type: string | null;
  status: RunStatus;
  created_at: string;
  updated_at: string;
}

export interface RunCreate {
  experiment_id: string;
  model_type?: string | null;
  training_configuration?: Record<string, unknown> | null;
  notes?: string | null;
}

export interface RunUpdate {
  model_type?: string | null;
  training_configuration?: Record<string, unknown> | null;
  notes?: string | null;
  status?: RunStatus;
}

// ─── Training Execution Types ───────────────────────────────────────────────────

export interface ExecuteRunRequest {
  target_column: string;
  test_split?: number;
}

export interface EvaluationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc?: number | null;
  confusion_matrix: number[][];
}

export interface ExecuteRunResponse {
  run_id: string;
  status: RunStatus;
  metrics: EvaluationMetrics;
  model_type: string | null;
}

