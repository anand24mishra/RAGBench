import React from 'react'

interface LatencyStage {
  label: string
  ms: number
  color?: string
}

interface LatencyBreakdownProps {
  stages: LatencyStage[]
  totalMs: number
}

export const LatencyBar: React.FC<LatencyBreakdownProps> = ({ stages, totalMs }) => {
  const safeTotal = Math.max(totalMs, 0.001)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {stages.map((stage) => {
        const percentage = Math.min(Math.max((stage.ms / safeTotal) * 100, 2), 100)
        return (
          <div
            key={stage.label}
            style={{
              display: 'grid',
              gridTemplateColumns: '90px 1fr 70px',
              alignItems: 'center',
              gap: 'var(--space-3)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
              {stage.label}
            </span>
            <div
              style={{
                height: 6,
                backgroundColor: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${percentage}%`,
                  backgroundColor: stage.color || 'var(--border-strong)',
                  borderRadius: 'var(--radius-sm)',
                  transition: 'width var(--transition-normal)',
                }}
              />
            </div>
            <span
              className="mono"
              style={{
                textAlign: 'right',
                color: 'var(--text-primary)',
                fontWeight: 500,
              }}
            >
              {stage.ms.toFixed(2)} ms
            </span>
          </div>
        )
      })}
    </div>
  )
}
