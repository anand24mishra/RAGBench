import React from 'react'
import { ArrowUpRight } from 'lucide-react'
import { Badge } from '../common/Badge'
import type { QueryEvaluationResult } from '../../types/evaluation'

interface EvaluationTableProps {
  queries: QueryEvaluationResult[]
  onSelectQuery?: (queryId: string) => void
}

export const EvaluationTable: React.FC<EvaluationTableProps> = ({
  queries,
  onSelectQuery,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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
          Per-Query Retrieval & Generation Results ({queries.length})
        </span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Click row to open Query Inspector
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: 'var(--text-xs)',
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                borderBottom: '1px solid var(--border-subtle)',
                color: 'var(--text-muted)',
                fontWeight: 600,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                fontSize: '11px',
              }}
            >
              <th style={{ padding: '8px 12px' }}>Query ID</th>
              <th style={{ padding: '8px 12px' }}>Question</th>
              <th style={{ padding: '8px 12px' }}>Target Evidence</th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>Target Rank</th>
              <th style={{ padding: '8px 12px', textAlign: 'center' }}>R@1</th>
              <th style={{ padding: '8px 12px', textAlign: 'center' }}>R@3</th>
              <th style={{ padding: '8px 12px', textAlign: 'center' }}>R@5</th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>MRR</th>
              <th style={{ padding: '8px 12px', textAlign: 'center' }}>Status</th>
              <th style={{ padding: '8px 12px', width: 40 }}></th>
            </tr>
          </thead>
          <tbody>
            {queries.map((q) => {
              // Find rank of the expected relevant document
              const expectedDoc = q.relevant_documents?.[0]
              const foundItem = q.retrieved?.find((r) => r.document_id === expectedDoc)
              const rank = foundItem ? foundItem.rank : null

              const isPass = q.recall_at_5 === 1.0 && q.reciprocal_rank >= 0.5
              const status = isPass ? 'pass' : 'inspect'

              return (
                <tr
                  key={q.query_id}
                  onClick={() => onSelectQuery && onSelectQuery(q.query_id)}
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    cursor: onSelectQuery ? 'pointer' : 'default',
                    transition: 'background-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-surface-hover)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <td style={{ padding: '8px 12px' }}>
                    <span className="mono" style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                      {q.query_id}
                    </span>
                  </td>

                  <td
                    style={{
                      padding: '8px 12px',
                      maxWidth: 320,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      color: 'var(--text-secondary)',
                    }}
                    title={q.question}
                  >
                    {q.question}
                  </td>

                  <td style={{ padding: '8px 12px' }}>
                    <span
                      className="mono"
                      style={{
                        color: 'var(--text-muted)',
                        backgroundColor: 'var(--bg-base)',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {expectedDoc || '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span
                      className="mono"
                      style={{
                        fontWeight: 600,
                        color: rank === 1 ? 'var(--success)' : rank && rank <= 3 ? 'var(--text-primary)' : 'var(--warning)',
                      }}
                    >
                      {rank !== null ? `#${rank}` : '> 5'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span style={{ color: q.recall_at_1 === 1 ? 'var(--success)' : 'var(--text-muted)' }}>
                      {q.recall_at_1 === 1 ? '✓' : '✕'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span style={{ color: q.recall_at_3 === 1 ? 'var(--success)' : 'var(--text-muted)' }}>
                      {q.recall_at_3 === 1 ? '✓' : '✕'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span style={{ color: q.recall_at_5 === 1 ? 'var(--success)' : 'var(--error)' }}>
                      {q.recall_at_5 === 1 ? '✓' : '✕'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                      {q.reciprocal_rank.toFixed(3)}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <Badge variant={status === 'pass' ? 'success' : 'warning'} size="sm">
                      {status}
                    </Badge>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-muted)' }}>
                    <ArrowUpRight size={13} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
