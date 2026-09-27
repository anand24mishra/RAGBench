import React, { useState } from 'react'
import { Play } from 'lucide-react'
import { Button } from '../common/Button'

interface QueryInputProps {
  onRunQuery: (query: string, topK: number) => void
  loading?: boolean
  defaultQuery?: string
  defaultTopK?: number
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onRunQuery,
  loading = false,
  defaultQuery = 'Which file formats does RAGBench V1 accept for ingestion?',
  defaultTopK = 5,
}) => {
  const [query, setQuery] = useState(defaultQuery)
  const [topK, setTopK] = useState(defaultTopK)

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!query.trim() || loading) return
    onRunQuery(query.trim(), topK)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSubmit()
    }
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label
          htmlFor="query-textarea"
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-muted)',
          }}
        >
          Query
        </label>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Press <kbd className="mono" style={{ backgroundColor: 'var(--bg-surface-elevated)', padding: '1px 4px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-medium)' }}>⌘+Enter</kbd> to run
        </span>
      </div>

      <textarea
        id="query-textarea"
        rows={3}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question against the indexed corpus..."
        style={{
          width: '100%',
          backgroundColor: 'var(--bg-base)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-sm)',
          padding: 'var(--space-3)',
          color: 'var(--text-primary)',
          fontSize: 'var(--text-sm)',
          lineHeight: 1.5,
          resize: 'vertical',
          minHeight: 72,
        }}
      />

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 500 }}>
              top_k:
            </span>
            <select
              aria-label="Top K candidates"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="mono"
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-sm)',
                padding: '3px 8px',
                fontSize: 'var(--text-xs)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              <option value={1}>1</option>
              <option value={3}>3</option>
              <option value={5}>5 (default)</option>
              <option value={10}>10</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 500 }}>
              configuration:
            </span>
            <span
              className="mono"
              style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--text-secondary)',
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              baseline (800c/100o)
            </span>
          </div>
        </div>

        <Button
          variant="primary"
          size="md"
          loading={loading}
          onClick={handleSubmit}
          icon={loading ? undefined : <Play size={12} fill="currentColor" />}
        >
          Run Query
        </Button>
      </div>
    </div>
  )
}
