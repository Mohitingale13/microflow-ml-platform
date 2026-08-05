// ai.types.ts — TypeScript interfaces for AI Run Review + Run Comparison.

// ─── Run Review ────────────────────────────────────────────────────────────────

export interface AIReviewContent {
  overall_assessment: string;
  strengths: string;
  weaknesses: string;
  comparison: string;
  recommendation: string;
}

export interface AIReviewResponse extends AIReviewContent {
  id: string;
  run_id: string;
  model_name: string;
  generated_at: string; // ISO datetime string
  cached: boolean;
}

// ─── Run Comparison ────────────────────────────────────────────────────────────

export type MetricDirection = 'up' | 'down' | 'equal' | 'unavailable';

export interface MetricDelta {
  metric: string;
  run_a_value: number | null;
  run_b_value: number | null;
  delta: number | null;         // run_b - run_a
  direction: MetricDirection;
}

export interface AIComparisonContent {
  overall_summary: string;
  better_run: string;
  key_improvements: string;
  tradeoffs: string;
  configuration_analysis: string;
  next_recommendation: string;
}

export interface AIComparisonResponse extends AIComparisonContent {
  id: string;
  run_a_id: string;
  run_b_id: string;
  metric_deltas: MetricDelta[];
  model_name: string;
  generated_at: string; // ISO datetime string
  cached: boolean;
}

// ─── Ask MicroFlow (Natural Language Assistant) ────────────────────────────────

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AIQueryRequest {
  question: string;
  context?: ConversationMessage[];
}

export interface AIQueryResponse {
  id: string;
  question: string;
  intent: string;
  answer: string;
  reasoning: string;
  supporting_data: string;
  recommendation: string | null;
  model_name: string;
  generated_at: string; // ISO datetime string
  cached: boolean;
}

