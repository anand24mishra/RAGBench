import React from 'react'

export interface MetricItem {
  label: string
  value: string | number | null | undefined
  subtext?: string
  delta?: number | null
  status?: 'pass' | 'fail' | 'neutral'
}

interface MetricStripProps {
  metrics: MetricItem[]
  columns?: number
}

export const MetricStrip: React.FC<MetricStripProps> = ({ metrics, columns }) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: columns ? `repeat(${columns}, 1fr)` : `repeat(auto-fit, minmax(130px, 1fr))`,
        gap: 'var(--space-3)',
        padding: 'var(--space-3) var(--space-4)',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      {metrics.map((m, idx) => {
        const formattedValue =
          typeof m.value === 'number'
            ? m.value.toFixed(3)
            : m.value !== null && m.value !== undefined
            ? String(m.value)
            : '—'

        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--text-muted)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              {m.label}
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span
                className="mono"
                style={{
                  fontSize: 'var(--text-lg)',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                {formattedValue}
              </span>
              {m.delta !== undefined && m.delta !== null && (
                <span
                  className="mono"
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 500,
                    color:
                      m.delta > 0
                        ? 'var(--success)'
                        : m.delta < 0
                        ? 'var(--error)'
                        : 'var(--text-muted)',
                  }}
                >
                  {m.delta > 0 ? `+${m.delta.toFixed(3)}` : m.delta.toFixed(3)}
                </span>
              )}
            </div>
            {m.subtext && (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                {m.subtext}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
