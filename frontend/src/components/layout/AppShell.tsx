import React from 'react'
import { Sidebar, type NavRoute } from './Sidebar'
import { TopBar } from './TopBar'
import type { SystemConfig } from '../../types/experiments'

interface AppShellProps {
  currentRoute: NavRoute
  onNavigate: (route: NavRoute) => void
  title: string
  datasetContext?: string
  systemConfig: SystemConfig | null
  apiOnline: boolean
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({
  currentRoute,
  onNavigate,
  title,
  datasetContext,
  systemConfig,
  apiOnline,
  children,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: 'var(--bg-base)',
      }}
    >
      <Sidebar
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        systemConfig={systemConfig}
        apiOnline={apiOnline}
      />

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          height: '100%',
          overflow: 'hidden',
        }}
      >
        <TopBar title={title} datasetContext={datasetContext} apiOnline={apiOnline} />

        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-6)',
          }}
        >
          <div
            style={{
              maxWidth: 'var(--workspace-max-width)',
              margin: '0 auto',
              width: '100%',
            }}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
