import { Terminal, BarChart2, GitPullRequest, Search, Upload } from 'lucide-react'
import { StatusDot } from '../common/StatusDot'
import type { SystemConfig } from '../../types/experiments'

export type NavRoute = 'query' | 'evaluation' | 'experiments' | 'inspector' | 'ingestion'

interface SidebarProps {
  currentRoute: NavRoute
  onNavigate: (route: NavRoute) => void
  systemConfig: SystemConfig | null
  apiOnline: boolean
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onNavigate,
  systemConfig,
  apiOnline,
}) => {
  const navItems: { id: NavRoute; label: string; section: string; icon: React.ReactNode }[] = [
    {
      id: 'query',
      section: 'QUERY',
      label: 'Query Console',
      icon: <Terminal size={14} />,
    },
    {
      id: 'evaluation',
      section: 'EVALUATION',
      label: 'Evaluation',
      icon: <BarChart2 size={14} />,
    },
    {
      id: 'experiments',
      section: 'EXPERIMENTS',
      label: 'Experiments',
      icon: <GitPullRequest size={14} />,
    },
    {
      id: 'ingestion',
      section: 'INGESTION',
      label: 'Upload Document',
      icon: <Upload size={14} />,
    },
    {
      id: 'inspector',
      section: 'INSPECTOR',
      label: 'Query Inspector',
      icon: <Search size={14} />,
    },
  ]

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        backgroundColor: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        height: '100%',
        userSelect: 'none',
      }}
    >
      <div>
        {/* Top Branding */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-4)',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: 'var(--text-md)',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
              }}
            >
              RAGBench
            </span>
            <span
              className="mono"
              style={{
                fontSize: 'var(--text-xs)',
                padding: '1px 5px',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
              }}
            >
              v0.1.0
            </span>
          </div>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              marginTop: '2px',
            }}
          >
            Evaluation Console
          </div>
        </div>

        {/* Navigation Section */}
        <nav style={{ padding: 'var(--space-3) var(--space-2)' }}>
          {navItems.map((item) => {
            const isActive = currentRoute === item.id
            return (
              <div key={item.id} style={{ marginBottom: 'var(--space-2)' }}>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    letterSpacing: '0.08em',
                    color: 'var(--text-muted)',
                    padding: '0 var(--space-2)',
                    display: 'block',
                    marginBottom: '4px',
                  }}
                >
                  {item.section}
                </span>
                <button
                  onClick={() => onNavigate(item.id)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '6px var(--space-2)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--text-sm)',
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    backgroundColor: isActive ? 'var(--bg-surface-elevated)' : 'transparent',
                    border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                    transition: 'all var(--transition-fast)',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)' }}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              </div>
            )
          })}
        </nav>
      </div>

      {/* Bottom System & Config */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderTop: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-base)',
          fontSize: 'var(--text-xs)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            SYSTEM
          </span>
          <StatusDot status={apiOnline ? 'online' : 'offline'} label={apiOnline ? 'Connected' : 'Offline'} />
        </div>

        {systemConfig && (
          <div
            className="mono"
            style={{
              fontSize: '10px',
              color: 'var(--text-muted)',
              lineHeight: 1.5,
              padding: '6px',
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div>chunk: {systemConfig.configuration.chunk_size}c / {systemConfig.configuration.chunk_overlap}o</div>
            <div>top_k: {systemConfig.configuration.top_k} | {systemConfig.configuration.vector_store}</div>
            <div style={{ color: 'var(--text-secondary)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {systemConfig.configuration.embedding_model.split('/').pop()}
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
