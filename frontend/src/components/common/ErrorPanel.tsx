import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from './Button'

interface ErrorPanelProps {
  title?: string
  message: string
  code?: string
  requestId?: string
  onRetry?: () => void
}

export const ErrorPanel: React.FC<ErrorPanelProps> = ({
  title = 'Request failed',
  message,
  code,
  requestId,
  onRetry,
}) => {
  return (
    <div
      style={{
        padding: 'var(--space-4)',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--error-border)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <AlertTriangle size={16} color="var(--error)" />
        <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--error)' }}>
          {title}
        </h4>
      </div>

      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
        {message}
      </p>

      {(code || requestId) && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--space-3)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-xs)',
          }}
        >
          {code && (
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Code: </span>
              <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                {code}
              </span>
            </div>
          )}
          {requestId && (
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Request ID: </span>
              <span className="mono" style={{ color: 'var(--text-primary)' }}>
                {requestId}
              </span>
            </div>
          )}
        </div>
      )}

      {onRetry && (
        <div>
          <Button variant="secondary" size="sm" onClick={onRetry} icon={<RefreshCw size={12} />}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  )
}
