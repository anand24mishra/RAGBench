export interface RetrievedDocumentResult {
  rank: number
  document_id: string
  raw_document_id: string
  chunk_id: string
  score: number
}

export interface GenerationMetrics {
  correctness: number
  faithfulness: number
  context_relevance: number
}

export type GenerationFailureType =
  | 'retrieval_failure'
  | 'context_failure'
  | 'generation_failure'
  | 'grounding_failure'
  | 'provider_failure'

export interface QueryEvaluationResult {
  query_id: string
  question: string
  relevant_documents: string[]
  retrieved: RetrievedDocumentResult[]
  retrieved_documents: string[]
  recall_at_1: number
  recall_at_3: number
  recall_at_5: number
  reciprocal_rank: number
  embedding_ms?: number | null
  retrieval_ms?: number | null
  candidate_count?: number | null
  context?: string | null
  generated_answer?: string | null
  reference_answer?: string | null
  generation_metrics?: GenerationMetrics | null
  generation_ms?: number | null
  total_ms?: number | null
  failure_classification?: GenerationFailureType | null
  input_tokens?: number | null
  output_tokens?: number | null
  total_tokens?: number | null
  input_cost?: number | null
  output_cost?: number | null
  total_cost?: number | null
  cost_status?: 'available' | 'unavailable'
}

export interface ReliabilityMetrics {
  total_requests: number
  successful_requests: number
  failed_requests: number
  failure_rate: number
  failure_categories: Record<string, number>
  timeouts: number
  provider_errors: number
}

export interface RetrievalFailure {
  query_id: string
  expected_document: string
  retrieved_documents: string[]
  retrieval_scores: number[]
}

export interface RetrieverConfiguration {
  chunk_size: number
  chunk_overlap: number
  embedding_batch_size: number
  distance: string
  vector_store: string
  qdrant_mode: string
  normalized_embeddings: boolean
}

export interface GenerationEvaluationStatus {
  status: 'not_implemented' | 'evaluated'
  metrics: string[]
  evaluator_type?: string | null
  generation_model?: string | null
  judge_model?: string | null
  aggregate_metrics: Record<string, number>
}

export interface EvaluationResult {
  schema_version?: string
  experiment_id: string
  timestamp: string
  dataset_name: string
  dataset_version: string
  dataset_fingerprint: string
  corpus_documents: Record<string, string>
  retriever_configuration: RetrieverConfiguration
  embedding_model: string
  software_versions: Record<string, string>
  top_k: number
  query_count: number
  metrics: {
    recall_at_1: number
    recall_at_3: number
    recall_at_5: number
    mrr: number
    [key: string]: number
  }
  queries: QueryEvaluationResult[]
  failures: RetrievalFailure[]
  generation_evaluation?: GenerationEvaluationStatus
  timing?: {
    mean_ms?: number
    p50_ms?: number
    p95_ms?: number
    p99_ms?: number
    embedding?: { mean_ms: number; p50_ms: number; p95_ms: number; p99_ms: number }
    retrieval?: { mean_ms: number; p50_ms: number; p95_ms: number; p99_ms: number }
    generation?: { mean_ms: number; p50_ms: number; p95_ms: number; p99_ms: number }
  }
  cost_accounting?: {
    total_tokens: number
    input_tokens: number
    output_tokens: number
    total_cost: number | null
    cost_status: 'available' | 'unavailable'
    cost_per_query: number | null
  }
  reliability?: ReliabilityMetrics
}

export interface RankingChange {
  query_id: string
  expected_document: string
  baseline_rank?: number | null
  experiment_rank?: number | null
  baseline_score?: number | null
  experiment_score?: number | null
}

export interface ComparisonResult {
  baseline_experiment_id: string
  experiment_id: string
  dataset_name: string
  dataset_version: string
  dataset_fingerprint: string
  baseline_metrics: Record<string, number>
  experiment_metrics: Record<string, number>
  metric_differences: Record<string, number>
  ranking_changes: RankingChange[]
  changed_parameter?: string | null
  interpretation?: string | null
  is_improvement?: boolean
}

export interface RegressionCheck {
  metric: string
  category: string
  baseline: number | null
  candidate: number | null
  delta: number | null
  threshold: number | null
  status: 'pass' | 'fail' | 'inconclusive'
  message: string
}

export interface RegressionDecision {
  status: 'pass' | 'fail' | 'inconclusive'
  baseline_id: string
  candidate_id: string
  dataset_version: string
  summary: string
  checks: RegressionCheck[]
  warnings: string[]
}
