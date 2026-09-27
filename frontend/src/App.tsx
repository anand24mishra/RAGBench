import React, { useEffect, useState } from 'react'
import { AppShell } from './components/layout/AppShell'
import type { NavRoute } from './components/layout/Sidebar'
import { QueryConsole } from './pages/QueryConsole'
import { EvaluationPage } from './pages/EvaluationPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { ExperimentInspectorPage } from './pages/ExperimentInspectorPage'
import { QueryInspectorPage } from './pages/QueryInspectorPage'
import { IngestionPage } from './pages/IngestionPage'
import { fetchSystemConfig } from './api/experiments'
import type { SystemConfig } from './types/experiments'

function getInitialRouteState(): {
  route: NavRoute
  experimentId: string | null
  queryId: string | null
} {
  if (typeof window === 'undefined') {
    return { route: 'query', experimentId: null, queryId: 'q001' }
  }
  const path = window.location.pathname.replace(/^\//, '') || window.location.hash.replace(/^#\/?/, '')
  if (path.startsWith('experiments/')) {
    return { route: 'experiments', experimentId: path.replace('experiments/', ''), queryId: null }
  }
  if (path.startsWith('inspect/')) {
    return { route: 'inspector', experimentId: null, queryId: path.replace('inspect/', '') }
  }
  if (path === 'evaluation') {
    return { route: 'evaluation', experimentId: null, queryId: null }
  }
  if (path === 'ingest' || path === 'ingestion') {
    return { route: 'ingestion', experimentId: null, queryId: null }
  }
  if (path === 'experiments') {
    return { route: 'experiments', experimentId: null, queryId: null }
  }
  return { route: 'query', experimentId: null, queryId: null }
}

export const App: React.FC = () => {
  const initial = getInitialRouteState()
  const [currentRoute, setCurrentRoute] = useState<NavRoute>(initial.route)
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(initial.experimentId)
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(initial.queryId || 'q001')
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null)
  const [apiOnline, setApiOnline] = useState(true)

  useEffect(() => {
    const handlePopState = () => {
      const state = getInitialRouteState()
      setCurrentRoute(state.route)
      setSelectedExperimentId(state.experimentId)
      if (state.queryId) setSelectedQueryId(state.queryId)
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    let active = true
    fetchSystemConfig()
      .then((cfg) => {
        if (!active) return
        setSystemConfig(cfg)
        setApiOnline(true)
      })
      .catch(() => {
        if (!active) return
        setApiOnline(false)
      })
    return () => {
      active = false
    }
  }, [])

  const navigateTo = (route: NavRoute) => {
    setCurrentRoute(route)
    setSelectedExperimentId(null)
    window.history.pushState({}, '', `/${route}`)
  }

  const navigateToExperiment = (id: string) => {
    setSelectedExperimentId(id)
    setCurrentRoute('experiments')
    window.history.pushState({}, '', `/experiments/${id}`)
  }

  const navigateToQueryInspect = (queryId: string) => {
    setSelectedQueryId(queryId)
    setCurrentRoute('inspector')
    window.history.pushState({}, '', `/inspect/${queryId}`)
  }

  const getPageTitle = () => {
    switch (currentRoute) {
      case 'query':
        return 'Query Console'
      case 'evaluation':
        return 'Evaluation Report Viewer'
      case 'experiments':
        return selectedExperimentId
          ? `Experiment Inspector: ${selectedExperimentId}`
          : 'Controlled Experiments'
      case 'inspector':
        return `Query Inspector: ${selectedQueryId || 'q001'}`
      case 'ingestion':
        return 'Document Ingestion'
      default:
        return 'RAGBench'
    }
  }

  const getDatasetContext = () => {
    if (currentRoute === 'evaluation' || currentRoute === 'experiments') {
      return 'dataset v1.0.0 (baseline)'
    }
    return undefined
  }

  return (
    <AppShell
      currentRoute={currentRoute}
      onNavigate={navigateTo}
      title={getPageTitle()}
      datasetContext={getDatasetContext()}
      systemConfig={systemConfig}
      apiOnline={apiOnline}
    >
      {currentRoute === 'query' && <QueryConsole />}
      {currentRoute === 'ingestion' && <IngestionPage />}

      {currentRoute === 'evaluation' && (
        <EvaluationPage onInspectQuery={navigateToQueryInspect} />
      )}

      {currentRoute === 'experiments' &&
        (selectedExperimentId ? (
          <ExperimentInspectorPage
            experimentId={selectedExperimentId}
            onBack={() => {
              setSelectedExperimentId(null)
              window.history.pushState({}, '', '/experiments')
            }}
            onInspectQuery={navigateToQueryInspect}
          />
        ) : (
          <ExperimentsPage onSelectExperiment={navigateToExperiment} />
        ))}

      {currentRoute === 'inspector' && (
        <QueryInspectorPage
          queryId={selectedQueryId || 'q001'}
          onBack={() => {
            navigateTo('evaluation')
          }}
        />
      )}
    </AppShell>
  )
}

export default App
