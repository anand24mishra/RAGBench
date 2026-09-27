import React from 'react'
import type { RAGResponse } from '../../types/rag'

interface QueryTraceProps {
  query: string
  response: RAGResponse | null
  loading: boolean
}

export const QueryTrace: React.FC<QueryTraceProps> = ({ query, response, loading }) => {
  if (!loading && !response) return null

  const steps = [
    {
      num: '01',
      stage: 'QUERY',
      detail: loading ? 'Processing query...' : `Input accepted ("${query.slice(0, 36)}${query.length > 36 ? '...' : ''}")`,
      status: loading ? 'active' : 'completed',
    },
    {
      num: '02',
      stage: 'EMBEDDING',
      detail: loading
        ? 'Generating dense vector embedding...'
        : response
        ? `sentence-transformers/all-MiniLM-L6-v2 (${response.latency.embedding_ms.toFixed(2)} ms)`
        : 'Pending',
      status: loading ? 'pending' : 'completed',
    },
    {
      num: '03',
      stage: 'RETRIEVAL',
      detail: loading
        ? 'Scanning vector index...'
        : response
        ? `${response.sources.length} chunks retrieved from Qdrant (${response.latency.retrieval_ms.toFixed(2)} ms)`
        : 'Pending',
      status: loading ? 'pending' : 'completed',
    },
    {
      num: '04',
      stage: 'CONTEXT',
      detail: loading
        ? 'Assembling context...'
        : response
        ? `${response.sources.reduce((acc, s) => acc + s.text.length, 0).toLocaleString()} characters assembled`
        : 'Pending',
      status: loading ? 'pending' : 'completed',
    },
    {
      num: '05',
      stage: 'GENERATION',
      detail: loading
        ? 'Generating grounded answer...'
        : response
        ? `${response.usage.model || 'mock-llm'} completed (${response.latency.generation_ms.toFixed(2)} ms)`
        : 'Pending',
      status: loading ? 'pending' : 'completed',
    },
    {
      num: '06',
      stage: 'RESULT',
      detail: loading ? 'Awaiting pipeline...' : response ? `Total latency: ${response.latency.total_ms.toFixed(2)} ms` : 'Pending',
      status: loading ? 'pending' : 'completed',
    },
  ]

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-3) var(--space-4)',
      }}
    >
      <div
        style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 600,
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          marginBottom: 'var(--space-2)',
        }}
      >
        Pipeline Execution Trace
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--space-2)',
        }}
      >
        {steps.map((s) => (
          <div
            key={s.num}
            style={{
              padding: '6px 10px',
              backgroundColor: s.status === 'active' ? 'var(--accent-subtle)' : 'var(--bg-base)',
              border: `1px solid ${
                s.status === 'active' ? 'var(--accent-border)' : 'var(--border-subtle)'
              }`,
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                className="mono"
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: s.status === 'completed' ? 'var(--success)' : 'var(--text-muted)',
                }}
              >
                {s.num}
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: s.status === 'active' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  letterSpacing: '0.04em',
                }}
              >
                {s.stage}
              </span>
            </div>
            <div
              style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                lineHeight: 1.3,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {s.detail}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
