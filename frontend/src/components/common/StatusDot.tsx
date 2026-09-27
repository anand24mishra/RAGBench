import React from 'react'

interface StatusDotProps {
  status: 'online' | 'offline' | 'pass' | 'fail' | 'inconclusive' | 'pending' | 'warning'
  label?: string
  size?: number
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, label, size = 7 }) => {
  const getColor = () => {
    switch (status) {
      case 'online':
      case 'pass':
        return 'var(--success)'
      case 'offline':
      case 'fail':
        return 'var(--error)'
      case 'warning':
      case 'inconclusive':
        return 'var(--warning)'
      case 'pending':
      default:
        return 'var(--text-muted)'
    }
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
      <span
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          backgroundColor: getColor(),
          display: 'inline-block',
          boxShadow: status === 'online' || status === 'pass' ? '0 0 6px rgba(16, 185, 129, 0.4)' : undefined,
        }}
      />
      {label && (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', fontWeight: 500 }}>
          {label}
        </span>
      )}
    </span>
  )
}
