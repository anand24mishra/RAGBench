import React from 'react'
import { Terminal } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
  icon?: React.ReactNode
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  icon = <Terminal size={20} color="var(--text-muted)" />,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-8) var(--space-4)',
        textAlign: 'center',
        backgroundColor: 'var(--bg-surface)',
        border: '1px dashed var(--border-medium)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div style={{ marginBottom: 'var(--space-2)' }}>{icon}</div>
      <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-secondary)' }}>
        {title}
      </h4>
      {description && (
        <p
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            marginTop: 'var(--space-1)',
            maxWidth: 380,
            lineHeight: 1.4,
          }}
        >
          {description}
        </p>
      )}
      {action && <div style={{ marginTop: 'var(--space-3)' }}>{action}</div>}
    </div>
  )
}
