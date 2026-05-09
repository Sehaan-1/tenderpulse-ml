export type TenderCategory = "Goods" | "Services" | "Works" | "Unclassified";

export interface CategoryCount {
  label: TenderCategory | string;
  count: number;
  color: string;
}

export interface ConfidenceBucket {
  label: string;
  min: number;
  max: number;
  count: number;
}

export interface MonthlyCategoryCount {
  [key: string]: string | number;
  month: string;
  Goods: number;
  Services: number;
  Works: number;
}

export interface TenderRecord {
  record_key: string;
  tender_id: string;
  title: string;
  clean_title?: string;
  reference_number?: string | null;
  org_chain?: string | null;
  tender_type?: string | null;
  category?: string | null;
  tender_value?: number | string | null;
  emd_amount?: number | string | null;
  currency?: string | null;
  closing_date?: string | null;
  opening_date?: string | null;
  published_date?: string | null;
  detail_url?: string | null;
  predicted_category: TenderCategory | string;
  category_confidence?: number | null;
}

export interface TenderListResponse {
  items: TenderRecord[];
  total: number;
  page: number;
  page_size: number;
  categories: string[];
  organizations: string[];
}

export interface AnalyticsSummary {
  total: number;
  category_counts: CategoryCount[];
  avg_confidence: number;
  confidence_buckets: ConfidenceBucket[];
  monthly_category_counts: MonthlyCategoryCount[];
  recent_tenders: TenderRecord[];
  accuracy: number;
  baseline_accuracy: number;
}

export interface ClassMetric {
  label: TenderCategory | string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
  color: string;
}

export interface FailureCount {
  label: string;
  count: number;
}

export interface WorstExample {
  tender_id?: string;
  title?: string;
  clean_title?: string;
  predicted_category?: string;
  actual_category?: string;
  category_confidence?: number | null;
  failure?: string;
}

export interface EvaluationResponse {
  labels: string[];
  metrics: ClassMetric[];
  confusion_matrix: number[][];
  failure_counts: FailureCount[];
  worst_examples: WorstExample[];
  representative_accuracy: number;
  strict_representative_accuracy: number;
  all_accuracy: number;
  dataset_baseline: number;
  annotated_count: number;
}

export interface ClassifyResponse {
  file_name: string;
  total: number;
  errors: Array<{ line: number; error: string }>;
  results: TenderRecord[];
  enriched_jsonl: string;
  category_counts: CategoryCount[];
  avg_confidence: number;
}
