import React from 'react'
import type { ComparisonResult } from '../../types/evaluation'

interface ComparisonViewProps {
  comparison: ComparisonResult
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ comparison }) => {
  const metricKeys = ['mrr', 'recall_at_1', 'recall_at_3', 'recall_at_5']

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
            }}
          >
            Baseline vs Candidate Comparison
          </span>
          <span
            className="mono"
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-secondary)',
              backgroundColor: 'var(--bg-surface-elevated)',
              padding: '1px 6px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            {comparison.baseline_experiment_id} → {comparison.experiment_id}
          </span>
        </div>

        <span
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            fontWeight: 500,
          }}
        >
          Measured change
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        {metricKeys.map((key) => {
          const baseVal = comparison.baseline_metrics[key] ?? 0
          const expVal = comparison.experiment_metrics[key] ?? 0
          const delta = comparison.metric_differences[key] ?? 0
          const label = key.toUpperCase().replace('_', ' ')

          return (
            <div
              key={key}
              style={{
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: 'var(--space-2) var(--space-3)',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                }}
              >
                {label}
              </div>

              <div
                className="mono"
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  justifyContent: 'space-between',
                  marginTop: 2,
                }}
              >
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                  {baseVal.toFixed(3)}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>→</span>
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {expVal.toFixed(3)}
                </span>
              </div>

              <div
                className="mono"
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textAlign: 'right',
                  color:
                    delta > 0
                      ? 'var(--success)'
                      : delta < 0
                      ? 'var(--error)'
                      : 'var(--text-muted)',
                }}
              >
                {delta > 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3)}
              </div>
            </div>
          )
        })}
      </div>

      {comparison.interpretation && (
        <div
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 10px',
            lineHeight: 1.4,
          }}
        >
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Analysis: </span>
          {comparison.interpretation}
        </div>
      )}
    </div>
  )
}
