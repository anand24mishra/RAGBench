import React from 'react'

export interface KeyValueItem {
  key: string
  value: React.ReactNode
  mono?: boolean
}

interface KeyValueGridProps {
  items: KeyValueItem[]
  columns?: number
}

export const KeyValueGrid: React.FC<KeyValueGridProps> = ({ items, columns = 2 }) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: 'var(--space-2) var(--space-4)',
        fontSize: 'var(--text-xs)',
      }}
    >
      {items.map((item, idx) => (
        <div
          key={idx}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            padding: '4px 0',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>{item.key}</span>
          <span
            className={item.mono !== false ? 'mono' : ''}
            style={{
              color: 'var(--text-primary)',
              fontWeight: 500,
              textAlign: 'right',
              maxWidth: '65%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  )
}
