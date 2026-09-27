import { requestJson } from './client'
import type { QueryRequest, RAGResponse } from '../types/rag'

export async function executeQuery(request: QueryRequest): Promise<RAGResponse> {
  return requestJson<RAGResponse>('/query', {
    method: 'POST',
    body: JSON.stringify(request),
    timeoutMs: 60000,
  })
}
