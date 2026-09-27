export interface ExperimentSummary {
  id: string
  type: 'chunking' | 'top_k' | 'embeddings' | string
  config_path?: string
  evaluated: boolean
  metrics?: {
    recall_at_1: number
    recall_at_3: number
    recall_at_5: number
    mrr: number
    [key: string]: number
  } | null
  timing?: {
    mean_ms?: number
    p50_ms?: number
    p95_ms?: number
    p99_ms?: number
  } | null
}

export interface SystemConfig {
  status: 'online' | 'offline'
  version: string
  python_version: string
  configuration: {
    chunk_size: number
    chunk_overlap: number
    top_k: number
    embedding_model: string
    generation_model: string
    vector_store: string
    environment: string
  }
}
