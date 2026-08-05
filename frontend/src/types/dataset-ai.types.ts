export interface RecommendedModel {
  model: string;
  suitability: 'High' | 'Medium' | 'Low' | string;
  reasoning: string;
}

export interface FeatureObservation {
  feature: string;
  observation: string;
}

export interface DatasetQuality {
  score: number;
  label: 'Excellent' | 'Good' | 'Fair' | 'Poor' | string;
  explanation?: string;
}

export interface DatasetAIAnalysis {
  id: string;
  dataset_id: string;
  overall_summary: string;
  recommended_target: string;
  dataset_quality: DatasetQuality | any;
  strengths: string[] | string;
  potential_issues: string[] | string;
  recommended_preprocessing: string[] | string;
  recommended_models: RecommendedModel[] | any[] | string;
  feature_observations: FeatureObservation[] | any[] | string;
  risk_assessment: string;
  next_steps: string[] | string;
  model_name: string;
  generated_at: string;
  cached: boolean;
}
