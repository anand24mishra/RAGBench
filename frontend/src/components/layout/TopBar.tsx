import React from 'react'
import { StatusDot } from '../common/StatusDot'

interface TopBarProps {
  title: string
  datasetContext?: string
  apiOnline: boolean
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  datasetContext = 'dataset v1.0.0 (baseline)',
  apiOnline,
}) => {
  return (
    <header
      style={{
        height: 'var(--topbar-height)',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <h1
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
            color: 'var(--text-primary)',
            letterSpacing: '-0.01em',
          }}
        >
          {title}
        </h1>
        {datasetContext && (
          <span
            className="mono"
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              padding: '2px 8px',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            {datasetContext}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          API
        </span>
        <StatusDot status={apiOnline ? 'online' : 'offline'} label={apiOnline ? 'Connected' : 'Offline'} />
      </div>
    </header>
  )
}
