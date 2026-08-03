/**
 * pipeline.types.ts — TypeScript interfaces for the Pipeline Visualization module.
 */

// ─── Node & Graph ─────────────────────────────────────────────────────────────

export type NodeStatus =
  | 'completed'
  | 'running'
  | 'failed'
  | 'pending'
  | 'queued'
  | 'skipped'
  | 'cancelled'
  | 'draft';

export interface PipelineNode {
  id: string;
  label: string;
  stage_type: string;
  status: NodeStatus;
  icon: string;
  color: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  detail: Record<string, unknown> | null;
  link: string | null;
}

export interface PipelineEdge {
  source: string;
  target: string;
  active: boolean;
}

export interface PipelineGraph {
  run_id: string;
  run_number: number;
  experiment_id: string;
  experiment_name: string;
  dataset_id: string | null;
  dataset_name: string | null;
  status: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

// ─── Timeline ─────────────────────────────────────────────────────────────────

export interface TimelineEvent {
  order: number;
  event: string;
  stage_type: string;
  status: NodeStatus;
  timestamp: string | null;
  duration_seconds: number | null;
  detail: string | null;
}

export interface PipelineTimeline {
  run_id: string;
  run_number: number;
  experiment_name: string;
  total_duration_seconds: number | null;
  events: TimelineEvent[];
}

// ─── Runs List ────────────────────────────────────────────────────────────────

export interface PipelineRunSummary {
  run_id: string;
  run_number: number;
  experiment_id: string;
  experiment_name: string;
  dataset_id: string | null;
  dataset_name: string | null;
  model: string | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  artifact_count: number;
  accuracy: number | null;
}

// ─── Overview ─────────────────────────────────────────────────────────────────

export interface PipelineOverview {
  total_pipelines: number;
  running: number;
  completed: number;
  failed: number;
  queued: number;
  draft: number;
  average_duration_seconds: number | null;
  total_artifacts_produced: number;
  success_rate: number;
}

// ─── Lineage ──────────────────────────────────────────────────────────────────

export interface LineageArtifact {
  artifact_id: string;
  artifact_type: string;
  filename: string;
  created_at: string | null;
}

export interface LineageRun {
  run_id: string;
  run_number: number;
  model: string | null;
  status: string;
  created_at: string | null;
  artifacts: LineageArtifact[];
}

export interface LineageExperiment {
  experiment_id: string;
  experiment_name: string;
  status: string;
  created_at: string | null;
  total_runs: number;
  completed_runs: number;
  runs: LineageRun[];
}

export interface LineageDataset {
  dataset_id: string;
  dataset_name: string;
  row_count: number | null;
  column_count: number | null;
  created_at: string | null;
  total_experiments: number;
  total_runs: number;
  experiments: LineageExperiment[];
}
