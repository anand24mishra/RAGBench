export interface QueryRequest {
  query: string
  top_k?: number
}

export interface SourceResponse {
  chunk_id: string
  document_id: string
  text: string
  score: floatNumber
  metadata: Record<string, unknown>
}

export type floatNumber = number

export interface LatencyResponse {
  embedding_ms: number
  retrieval_ms: number
  generation_ms: number
  total_ms: number
}

export interface UsageResponse {
  model: string | null
  input_tokens: number | null
  output_tokens: number | null
}

export interface RAGResponse {
  answer: string
  sources: SourceResponse[]
  latency: LatencyResponse
  usage: UsageResponse
}

export interface ErrorDetail {
  code: string
  message: string
  request_id: string
}

export interface ErrorResponse {
  detail: ErrorDetail
}

export interface TraceStep {
  id: string
  number: string
  name: string
  status: 'pending' | 'active' | 'completed' | 'failed'
  detail: string
  timing_ms?: number
}
