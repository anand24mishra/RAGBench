import React from 'react'

interface SkeletonProps {
  height?: number | string
  width?: number | string
  style?: React.CSSProperties
}

export const Skeleton: React.FC<SkeletonProps> = ({ height = 18, width = '100%', style }) => {
  return (
    <div
      style={{
        height,
        width,
        backgroundColor: 'var(--bg-surface-elevated)',
        borderRadius: 'var(--radius-sm)',
        opacity: 0.6,
        animation: 'pulse 1.5s ease-in-out infinite',
        ...style,
      }}
    />
  )
}
