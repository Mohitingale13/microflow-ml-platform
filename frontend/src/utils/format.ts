export const MODEL_TYPE_LABELS: Record<string, string> = {
  random_forest: 'Random Forest',
  logistic_regression: 'Logistic Regression',
  xgboost: 'XGBoost',
  lightgbm: 'LightGBM',
  svm: 'Support Vector Machine (SVM)',
  neural_network: 'Neural Network',
  gradient_boosting: 'Gradient Boosting',
  decision_tree: 'Decision Tree',
  linear_regression: 'Linear Regression',
};

export const SUPPORTED_MODELS = [
  { value: 'random_forest', label: 'Random Forest' },
  { value: 'logistic_regression', label: 'Logistic Regression' },
  { value: 'xgboost', label: 'XGBoost' },
] as const;

export function formatModelType(modelType: string | null | undefined): string {
  if (!modelType) return '—';
  if (MODEL_TYPE_LABELS[modelType]) {
    return MODEL_TYPE_LABELS[modelType];
  }
  return modelType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatBytes(bytes: number | null | undefined, decimals = 1): string {
  if (bytes === null || bytes === undefined || isNaN(bytes)) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const idx = Math.min(Math.max(0, i), sizes.length - 1);
  return `${parseFloat((bytes / Math.pow(k, idx)).toFixed(dm))} ${sizes[idx]}`;
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

