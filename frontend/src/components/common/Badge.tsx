import React from 'react'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'neutral' | 'success' | 'warning' | 'error' | 'accent'
  mono?: boolean
  size?: 'sm' | 'md'
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  mono = false,
  size = 'sm',
}) => {
  const getColors = () => {
    switch (variant) {
      case 'success':
        return {
          bg: 'var(--success-subtle)',
          border: 'var(--success-border)',
          color: 'var(--success)',
        }
      case 'warning':
        return {
          bg: 'var(--warning-subtle)',
          border: 'var(--warning-border)',
          color: 'var(--warning)',
        }
      case 'error':
        return {
          bg: 'var(--error-subtle)',
          border: 'var(--error-border)',
          color: 'var(--error)',
        }
      case 'accent':
        return {
          bg: 'var(--accent-subtle)',
          border: 'var(--accent-border)',
          color: 'var(--accent-primary)',
        }
      case 'neutral':
      default:
        return {
          bg: 'var(--bg-surface-elevated)',
          border: 'var(--border-medium)',
          color: 'var(--text-secondary)',
        }
    }
  }

  const { bg, border, color } = getColors()

  return (
    <span
      className={mono ? 'mono' : ''}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: size === 'sm' ? '2px 6px' : '3px 8px',
        fontSize: size === 'sm' ? 'var(--text-xs)' : 'var(--text-sm)',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color,
        fontWeight: 500,
        lineHeight: 1.2,
      }}
    >
      {children}
    </span>
  )
}
