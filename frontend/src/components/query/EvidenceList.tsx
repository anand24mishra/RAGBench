import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Copy, Check, FileText } from 'lucide-react'
import type { SourceResponse } from '../../types/rag'

interface EvidenceListProps {
  sources: SourceResponse[]
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ sources }) => {
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({
    0: true, // first chunk expanded by default
  })
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }))
  }

  const handleCopy = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 1500)
    } catch {
      // ignore
    }
  }

  if (sources.length === 0) {
    return (
      <div
        style={{
          padding: 'var(--space-6)',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: 'var(--text-sm)',
        }}
      >
        No evidence retrieved. The query did not return matching candidate chunks.
      </div>
    )
  }

  return (
    <section
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
        <h2
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-muted)',
          }}
        >
          Retrieved Evidence ({sources.length} chunks)
        </h2>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Ranked by cosine similarity
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {sources.map((source, idx) => {
          const isExpanded = !!expandedIndices[idx]
          const rankNum = String(idx + 1).padStart(2, '0')
          const filename =
            (source.metadata?.filename as string) ||
            (source.metadata?.source as string) ||
            source.document_id

          return (
            <div
              key={source.chunk_id}
              style={{
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
                transition: 'border-color var(--transition-fast)',
              }}
            >
              {/* Header row */}
              <div
                onClick={() => toggleExpand(idx)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  backgroundColor: isExpanded ? 'var(--bg-surface-elevated)' : 'transparent',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <span
                    className="mono"
                    style={{
                      fontSize: 'var(--text-xs)',
                      fontWeight: 700,
                      color: idx === 0 ? 'var(--accent-primary)' : 'var(--text-muted)',
                    }}
                  >
                    {rankNum}
                  </span>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={13} color="var(--text-muted)" />
                    <span
                      className="mono"
                      style={{
                        fontSize: 'var(--text-sm)',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {filename}
                    </span>
                  </div>

                  <span
                    className="mono"
                    style={{
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      backgroundColor: 'var(--bg-surface)',
                      padding: '1px 5px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    {source.chunk_id.slice(0, 8)}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>score</span>
                    <span
                      className="mono"
                      style={{
                        fontSize: 'var(--text-xs)',
                        fontWeight: 600,
                        color: source.score >= 0.7 ? 'var(--success)' : 'var(--text-secondary)',
                      }}
                    >
                      {source.score.toFixed(4)}
                    </span>
                  </div>

                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </span>
                </div>
              </div>

              {/* Chunk Content */}
              {isExpanded ? (
                <div
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                  }}
                >
                  <p
                    style={{
                      fontSize: 'var(--text-sm)',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {source.text}
                  </p>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: 'var(--space-2)',
                      paddingTop: 'var(--space-2)',
                      borderTop: '1px dashed var(--border-subtle)',
                      fontSize: '11px',
                    }}
                  >
                    <div className="mono" style={{ color: 'var(--text-muted)' }}>
                      doc_id: {source.document_id} | chars: {source.text.length}
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCopy(source.text, source.chunk_id)
                      }}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        color: copiedId === source.chunk_id ? 'var(--success)' : 'var(--text-secondary)',
                        fontSize: '11px',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {copiedId === source.chunk_id ? <Check size={11} /> : <Copy size={11} />}
                      <span>{copiedId === source.chunk_id ? 'Copied' : 'Copy chunk'}</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={() => toggleExpand(idx)}
                  style={{
                    padding: '4px 12px 8px 36px',
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    cursor: 'pointer',
                  }}
                >
                  "{source.text.slice(0, 110)}..."
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
