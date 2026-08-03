export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  version: string;
  original_filename: string;
  file_hash: string;
  file_size_bytes: number;
  row_count: number | null;
  column_count: number | null;
  storage_path: string;
  status: 'uploaded' | 'analysing' | 'ready' | 'error';
  column_names: string[] | null;
  dtypes: Record<string, string> | null;
  missing_values: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

export interface DatasetListItem {
  id: string;
  name: string;
  description: string | null;
  version: string;
  original_filename: string;
  file_size_bytes: number;
  row_count: number | null;
  column_count: number | null;
  status: 'uploaded' | 'analysing' | 'ready' | 'error';
  created_at: string;
  updated_at: string;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, any>[];
  total_rows: number | null;
}

export interface NumericColumnStat {
  type: 'numeric';
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  std: number | null;
  missing_count: number;
}

export interface CategoricalColumnStat {
  type: 'categorical';
  unique_values: number;
  most_frequent: string | null;
  missing_count: number;
}

export type ColumnStat = NumericColumnStat | CategoricalColumnStat;

export interface DatasetStatistics {
  dataset_id: string;
  statistics: Record<string, ColumnStat>;
}
