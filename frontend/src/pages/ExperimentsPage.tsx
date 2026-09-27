import React, { useEffect, useState } from 'react'
import { ExperimentsTable } from '../components/experiments/ExperimentsTable'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorPanel } from '../components/common/ErrorPanel'
import { fetchExperiments } from '../api/experiments'
import type { ExperimentSummary } from '../types/experiments'
import { MOCK_EXPERIMENTS } from '../api/mockData'

interface ExperimentsPageProps {
  onSelectExperiment: (id: string) => void
}

export const ExperimentsPage: React.FC<ExperimentsPageProps> = ({ onSelectExperiment }) => {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>(MOCK_EXPERIMENTS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const data = await fetchExperiments()
        if (!active) return
        setExperiments(data)
      } catch (err: unknown) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to fetch experiment list.')
      }
    }
    load()
    return () => {
      active = false
    }
  }, [])

  const handleRetry = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchExperiments()
      setExperiments(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch experiment list.')
    } finally {
      setLoading(false)
    }
  }

  if (loading && experiments.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <Skeleton height={40} />
        <Skeleton height={280} />
      </div>
    )
  }

  if (error && experiments.length === 0) {
    return <ErrorPanel title="Experiments error" message={error} onRetry={handleRetry} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div>
          <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
            Controlled Retrieval Experiments
          </h2>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
            Single-variable benchmark results across chunk sizes, top-k candidates, and embedding models.
          </p>
        </div>
      </div>

      <ExperimentsTable experiments={experiments} onSelectExperiment={onSelectExperiment} />
    </div>
  )
}
