import React from 'react'
import { KeyValueGrid } from '../common/KeyValueGrid'

interface RequestDetailsProps {
  requestId?: string | null
  embeddingModel?: string
  generationModel?: string | null
  topK?: number
  chunkSize?: number
  chunkOverlap?: number
}

export const RequestDetails: React.FC<RequestDetailsProps> = ({
  requestId = 'req_manual_session',
  embeddingModel = 'sentence-transformers/all-MiniLM-L6-v2',
  generationModel = 'mock-llm',
  topK = 5,
  chunkSize = 800,
  chunkOverlap = 100,
}) => {
  const items = [
    { key: 'Request ID', value: requestId || '—', mono: true },
    { key: 'Embedding model', value: embeddingModel.split('/').pop() || embeddingModel, mono: true },
    { key: 'Generation model', value: generationModel || '—', mono: true },
    { key: 'Top K candidates', value: String(topK), mono: true },
    { key: 'Chunking', value: `${chunkSize}c / ${chunkOverlap}o`, mono: true },
    { key: 'Vector store', value: 'Qdrant (memory, cosine)', mono: true },
  ]

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
      }}
    >
      <div
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 'var(--space-2)',
        }}
      >
        <span
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-muted)',
          }}
        >
          Request Details
        </span>
      </div>

      <KeyValueGrid items={items} columns={2} />
    </div>
  )
}
