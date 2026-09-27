import React, { useState } from 'react'
import { Copy, Check } from 'lucide-react'

interface CodeBlockProps {
  code: string
  title?: string
  language?: string
  maxHeight?: number | string
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  title,
  maxHeight = 320,
}) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      // ignore
    }
  }

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-base)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        fontSize: 'var(--text-xs)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 10px',
          backgroundColor: 'var(--bg-surface-elevated)',
          borderBottom: '1px solid var(--border-subtle)',
          color: 'var(--text-muted)',
        }}
      >
        <span className="mono" style={{ fontWeight: 500 }}>
          {title || 'JSON'}
        </span>
        <button
          onClick={handleCopy}
          title="Copy to clipboard"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            color: copied ? 'var(--success)' : 'var(--text-secondary)',
            fontSize: 'var(--text-xs)',
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre
        className="mono"
        style={{
          padding: 'var(--space-3)',
          overflowX: 'auto',
          maxHeight,
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        <code>{code}</code>
      </pre>
    </div>
  )
}
