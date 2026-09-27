import { requestJson } from './client'

export interface IngestResponse {
  document_id: string
  chunk_count: number
  status: string
}

export async function ingestDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return requestJson<IngestResponse>('/ingest', {
    method: 'POST',
    body: formData as any,
    timeoutMs: 120000,
  })
}
