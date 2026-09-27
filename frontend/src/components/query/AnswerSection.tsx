import React, { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { Badge } from '../common/Badge'

interface AnswerSectionProps {
  answer: string
  model?: string | null
  requestId?: string | null
  isGrounded?: boolean
}

export const AnswerSection: React.FC<AnswerSectionProps> = ({
  answer,
  model,
  requestId,
  isGrounded = true,
}) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      // ignore
    }
  }

  return (
    <section
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--space-3)',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 'var(--space-2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <h2
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
            }}
          >
            Answer
          </h2>
          {model && (
            <span className="mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              model: {model}
            </span>
          )}
          {requestId && (
            <span
              className="mono"
              style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                maxWidth: 160,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={requestId}
            >
              req: {requestId}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {isGrounded && model ? (
            <Badge variant="success" size="sm">
              Grounded
            </Badge>
          ) : (
            <Badge variant="neutral" size="sm">
              Generation Skipped
            </Badge>
          )}
          <button
            onClick={handleCopy}
            title="Copy answer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 'var(--text-xs)',
              color: copied ? 'var(--success)' : 'var(--text-secondary)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface-elevated)',
            }}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      <div
        style={{
          fontSize: 'var(--text-base)',
          color: 'var(--text-primary)',
          lineHeight: 1.6,
          letterSpacing: '-0.005em',
        }}
      >
        {answer}
      </div>
    </section>
  )
}
