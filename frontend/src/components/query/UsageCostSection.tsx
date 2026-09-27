import React from 'react'
import type { UsageResponse } from '../../types/rag'

interface UsageCostSectionProps {
  usage: UsageResponse
}

export const UsageCostSection: React.FC<UsageCostSectionProps> = ({ usage }) => {
  const inputTokens = usage.input_tokens
  const outputTokens = usage.output_tokens
  const totalTokens =
    inputTokens !== null && inputTokens !== undefined && outputTokens !== null && outputTokens !== undefined
      ? inputTokens + outputTokens
      : null

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
          Usage & Cost
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: 'var(--space-3)',
          fontSize: 'var(--text-xs)',
        }}
      >
        <div>
          <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Input tokens</div>
          <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {inputTokens !== null && inputTokens !== undefined ? inputTokens.toLocaleString() : '—'}
          </div>
        </div>

        <div>
          <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Output tokens</div>
          <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {outputTokens !== null && outputTokens !== undefined ? outputTokens.toLocaleString() : '—'}
          </div>
        </div>

        <div>
          <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Total tokens</div>
          <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {totalTokens !== null ? totalTokens.toLocaleString() : '—'}
          </div>
        </div>

        <div>
          <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Estimated cost</div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontStyle: 'italic', paddingTop: 4 }}>
            Not measured
          </div>
        </div>
      </div>
    </div>
  )
}
