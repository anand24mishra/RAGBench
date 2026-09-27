import React, { useState } from 'react'
import { ArrowUpDown, ArrowUpRight } from 'lucide-react'
import { Badge } from '../common/Badge'
import type { ExperimentSummary } from '../../types/experiments'

interface ExperimentsTableProps {
  experiments: ExperimentSummary[]
  onSelectExperiment: (id: string) => void
}

type SortField = 'id' | 'type' | 'mrr' | 'recall_at_5' | 'p50'

export const ExperimentsTable: React.FC<ExperimentsTableProps> = ({
  experiments,
  onSelectExperiment,
}) => {
  const [selectedFamily, setSelectedFamily] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('mrr')
  const [sortAsc, setSortAsc] = useState(false)

  const families = ['all', 'chunking', 'top_k', 'embeddings']

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  const filtered = experiments.filter((e) =>
    selectedFamily === 'all' ? true : e.type === selectedFamily
  )

  const sorted = [...filtered].sort((a, b) => {
    let aVal = 0
    let bVal = 0
    if (sortField === 'mrr') {
      aVal = a.metrics?.mrr ?? 0
      bVal = b.metrics?.mrr ?? 0
    } else if (sortField === 'recall_at_5') {
      aVal = a.metrics?.recall_at_5 ?? 0
      bVal = b.metrics?.recall_at_5 ?? 0
    } else if (sortField === 'p50') {
      aVal = a.timing?.p50_ms ?? 999
      bVal = b.timing?.p50_ms ?? 999
    } else if (sortField === 'id') {
      return sortAsc ? a.id.localeCompare(b.id) : b.id.localeCompare(a.id)
    } else if (sortField === 'type') {
      return sortAsc ? a.type.localeCompare(b.type) : b.type.localeCompare(a.type)
    }
    return sortAsc ? aVal - bVal : bVal - aVal
  })

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}
    >
      {/* Filter and Controls Header */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
              marginRight: 'var(--space-2)',
            }}
          >
            Family:
          </span>
          {families.map((fam) => {
            const isSelected = selectedFamily === fam
            return (
              <button
                key={fam}
                onClick={() => setSelectedFamily(fam)}
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: isSelected ? 600 : 400,
                  color: isSelected ? 'var(--text-primary)' : 'var(--text-muted)',
                  backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'transparent',
                  border: `1px solid ${isSelected ? 'var(--border-medium)' : 'transparent'}`,
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  textTransform: 'capitalize',
                  cursor: 'pointer',
                }}
              >
                {fam === 'top_k' ? 'Top-K' : fam}
              </button>
            )
          })}
        </div>

        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Showing {sorted.length} experiments | Click row to inspect
        </span>
      </div>

      {/* Table */}
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
              <th
                onClick={() => handleSort('id')}
                style={{ padding: '8px 12px', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Experiment</span>
                  <ArrowUpDown size={11} />
                </div>
              </th>
              <th
                onClick={() => handleSort('type')}
                style={{ padding: '8px 12px', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>Variable</span>
                  <ArrowUpDown size={11} />
                </div>
              </th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>R@1</th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>R@3</th>
              <th
                onClick={() => handleSort('recall_at_5')}
                style={{ padding: '8px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                  <span>R@5</span>
                  <ArrowUpDown size={11} />
                </div>
              </th>
              <th
                onClick={() => handleSort('mrr')}
                style={{ padding: '8px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                  <span>MRR</span>
                  <ArrowUpDown size={11} />
                </div>
              </th>
              <th
                onClick={() => handleSort('p50')}
                style={{ padding: '8px 12px', textAlign: 'right', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                  <span>p50 Latency</span>
                  <ArrowUpDown size={11} />
                </div>
              </th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>p95 Latency</th>
              <th style={{ padding: '8px 12px', textAlign: 'center' }}>Status</th>
              <th style={{ padding: '8px 12px', width: 40 }}></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((exp) => {
              const mrr = exp.metrics?.mrr
              const r1 = exp.metrics?.recall_at_1
              const r3 = exp.metrics?.recall_at_3
              const r5 = exp.metrics?.recall_at_5
              const p50 = exp.timing?.p50_ms
              const p95 = exp.timing?.p95_ms

              return (
                <tr
                  key={exp.id}
                  onClick={() => onSelectExperiment(exp.id)}
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    cursor: 'pointer',
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
                      {exp.id}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px' }}>
                    <span
                      style={{
                        color: 'var(--text-muted)',
                        backgroundColor: 'var(--bg-base)',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                        textTransform: 'capitalize',
                      }}
                    >
                      {exp.type.replace('_', '-')}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                      {r1 !== undefined ? r1.toFixed(3) : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                      {r3 !== undefined ? r3.toFixed(3) : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span
                      className="mono"
                      style={{
                        fontWeight: 600,
                        color: r5 === 1 ? 'var(--success)' : 'var(--text-primary)',
                      }}
                    >
                      {r5 !== undefined ? r5.toFixed(3) : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span
                      className="mono"
                      style={{
                        fontWeight: 700,
                        color: mrr && mrr >= 0.95 ? 'var(--success)' : 'var(--text-primary)',
                      }}
                    >
                      {mrr !== undefined ? mrr.toFixed(3) : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                      {p50 !== undefined ? `${p50.toFixed(2)} ms` : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    <span className="mono" style={{ color: 'var(--text-muted)' }}>
                      {p95 !== undefined ? `${p95.toFixed(2)} ms` : '—'}
                    </span>
                  </td>

                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <Badge variant={exp.evaluated ? 'success' : 'neutral'} size="sm">
                      {exp.evaluated ? 'Measured' : 'Pending'}
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
