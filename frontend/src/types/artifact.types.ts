// ─── Artifact Registry Types ───────────────────────────────────────────────────

export type ArtifactType =
  | 'trained_model'
  | 'metrics_json'
  | 'evaluation_json'
  | 'confusion_matrix_json'
  | 'configuration_json'
  | 'preprocessing_json'
  | 'shap_summary_png'
  | 'feature_importance_png'
  | 'shap_dependence_png'
  | 'shap_values_json'
  | 'feature_importance_json'
  | 'explainability_summary_json';

export interface Artifact {
  id: string;
  run_id: string;
  experiment_id: string;
  dataset_id: string;
  artifact_type: ArtifactType;
  filename: string;
  file_size_bytes: number;
  created_at: string;
}

export interface ArtifactDetail extends Artifact {
  mime_type: string;
  storage_path: string;
  sha256_checksum: string;
}

export interface RunResult {
  id: string;
  run_id: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number | null;
  confusion_matrix: number[][];
  execution_time_seconds: number | null;
  started_at: string | null;
  completed_at: string | null;
  model_type: string | null;
  dataset_id: string | null;
  training_config_snapshot: Record<string, unknown> | null;
  preprocessing_summary: Record<string, unknown> | null;
  explainability_status: string | null;
  explainability_error: string | null;
  explainability_summary: Record<string, unknown> | null;
  created_at: string;
}

export interface ArtifactRegistryStats {
  total_artifacts: number;
  models_stored: number;
  json_reports: number;
  total_size_bytes: number;
}
