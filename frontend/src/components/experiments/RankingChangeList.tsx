import React from 'react'
import { ArrowRight } from 'lucide-react'
import type { RankingChange } from '../../types/evaluation'

interface RankingChangeListProps {
  rankingChanges: RankingChange[]
  onInspectQuery?: (queryId: string) => void
}

export const RankingChangeList: React.FC<RankingChangeListProps> = ({
  rankingChanges,
  onInspectQuery,
}) => {
  if (rankingChanges.length === 0) {
    return (
      <div
        style={{
          padding: 'var(--space-4)',
          backgroundColor: 'var(--bg-base)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
          textAlign: 'center',
        }}
      >
        No rank movements observed relative to baseline.
      </div>
    )
  }

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
          Ranking Change Analysis ({rankingChanges.length} shifts)
        </span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Target document position shift
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {rankingChanges.map((change) => {
          const baseRank = change.baseline_rank ?? 999
          const expRank = change.experiment_rank ?? 999
          const improved = expRank < baseRank
          const regressed = expRank > baseRank

          return (
            <div
              key={change.query_id}
              onClick={() => onInspectQuery && onInspectQuery(change.query_id)}
              style={{
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: onInspectQuery ? 'pointer' : 'default',
                transition: 'border-color var(--transition-fast)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                <span className="mono" style={{ fontWeight: 600, color: 'var(--accent-primary)', fontSize: 'var(--text-sm)' }}>
                  {change.query_id}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>target:</span>
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
                    {change.expected_document}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)' }}>
                {/* Score change */}
                {change.baseline_score !== null &&
                  change.baseline_score !== undefined &&
                  change.experiment_score !== null &&
                  change.experiment_score !== undefined && (
                    <div className="mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                      <span>{change.baseline_score.toFixed(4)}</span>
                      <span style={{ margin: '0 4px' }}>→</span>
                      <span style={{ color: 'var(--text-primary)' }}>{change.experiment_score.toFixed(4)}</span>
                    </div>
                  )}

                {/* Rank Movement */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div
                    className="mono"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 'var(--text-sm)',
                      fontWeight: 600,
                    }}
                  >
                    <span style={{ color: 'var(--text-muted)' }}>
                      rank {change.baseline_rank ?? '>5'}
                    </span>
                    <ArrowRight size={13} color="var(--text-muted)" />
                    <span
                      style={{
                        color: improved
                          ? 'var(--success)'
                          : regressed
                          ? 'var(--error)'
                          : 'var(--text-primary)',
                      }}
                    >
                      rank {change.experiment_rank ?? '>5'}
                    </span>
                  </div>

                  <span
                    className="mono"
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: improved
                        ? 'var(--success)'
                        : regressed
                        ? 'var(--error)'
                        : 'var(--text-muted)',
                      backgroundColor: improved
                        ? 'var(--success-subtle)'
                        : regressed
                        ? 'var(--error-subtle)'
                        : 'var(--bg-surface)',
                      border: `1px solid ${
                        improved
                          ? 'var(--success-border)'
                          : regressed
                          ? 'var(--error-border)'
                          : 'var(--border-subtle)'
                      }`,
                      padding: '1px 5px',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {improved ? `+${baseRank - expRank}` : `${baseRank - expRank}`}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
