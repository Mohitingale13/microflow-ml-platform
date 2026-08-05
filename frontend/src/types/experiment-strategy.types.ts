export interface RecommendedNextExperiment {
  action: string;
  model_type?: string;
  hyperparameters?: Record<string, any>;
  rationale?: string;
}

export interface EvidenceSummary {
  dataset_summary?: {
    row_count: number;
    column_count: number;
    file_size_bytes: number;
    version: number;
    ai_insights?: {
      overall_summary?: string;
      recommended_target?: string;
      quality?: { score: number; label: string };
    };
  };
  run_counts: {
    completed: number;
    failed: number;
    in_progress: number;
  };
  metrics_analysis?: {
    average_accuracy?: number;
    best_accuracy?: number;
    best_accuracy_run?: string;
    average_f1?: number;
    best_f1?: number;
    accuracy_variance?: number;
    accuracy_std_dev?: number;
    fastest_execution?: string;
    slowest_execution?: string;
  };
  configurations_tested?: Array<{
    run_number: number;
    model: string;
    accuracy: number;
    f1_score: number;
    parameters: Record<string, any>;
  }>;
  search_space?: {
    evaluated_model_families?: string[];
    unexplored_model_families?: string[];
    untested_parameter_regions?: string[];
  };
  trend_and_plateau_analysis?: {
    plateau_detected?: boolean;
    improvement_trend?: string;
    stopping_guidance?: string;
  };
}

export interface ExperimentStrategy {
  id: string;
  experiment_id: string;
  overall_assessment: string;
  current_experiment_status: string;
  observed_trends: string[] | string;
  strongest_model: string;
  most_stable_model: string;
  what_has_been_learned: string[] | string;
  remaining_search_space: string[] | string;
  recommended_next_experiment: RecommendedNextExperiment | string;
  confidence: 'High' | 'Medium' | 'Low' | string;
  evidence_used: string[] | any[] | string;
  potential_risks: string[] | string;
  model_name: string;
  generated_at: string;
  cached: boolean;
  evidence_summary?: EvidenceSummary;
}
