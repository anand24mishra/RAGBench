import React from 'react'
import { LatencyBar } from '../common/LatencyBar'
import type { LatencyResponse } from '../../types/rag'

interface LatencyBreakdownProps {
  latency: LatencyResponse
}

export const LatencyBreakdown: React.FC<LatencyBreakdownProps> = ({ latency }) => {
  const stages = [
    { label: 'Embedding', ms: latency.embedding_ms, color: '#3b82f6' },
    { label: 'Retrieval', ms: latency.retrieval_ms, color: '#10b981' },
    { label: 'Generation', ms: latency.generation_ms, color: '#8b5cf6' },
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
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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
          Latency
        </span>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>total:</span>
          <span className="mono" style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {latency.total_ms.toFixed(2)} ms
          </span>
        </div>
      </div>

      <LatencyBar stages={stages} totalMs={latency.total_ms} />
    </div>
  )
}
