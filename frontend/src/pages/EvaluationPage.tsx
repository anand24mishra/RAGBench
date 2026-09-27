import React, { useEffect, useState } from 'react'
import { EvaluationSummary } from '../components/evaluation/EvaluationSummary'
import { ComparisonView } from '../components/evaluation/ComparisonView'
import { EvaluationTable } from '../components/evaluation/EvaluationTable'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorPanel } from '../components/common/ErrorPanel'
import { fetchBaselineEvaluation, fetchRegressionDecision } from '../api/evaluation'
import { fetchExperimentComparison } from '../api/experiments'
import type { EvaluationResult, ComparisonResult, RegressionDecision } from '../types/evaluation'
import { MOCK_BASELINE_EVALUATION, MOCK_EXPERIMENT_COMPARISON } from '../api/mockData'

interface EvaluationPageProps {
  onInspectQuery: (queryId: string) => void
}

export const EvaluationPage: React.FC<EvaluationPageProps> = ({ onInspectQuery }) => {
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(MOCK_BASELINE_EVALUATION)
  const [comparison, setComparison] = useState<ComparisonResult | null>(MOCK_EXPERIMENT_COMPARISON)
  const [regression, setRegression] = useState<RegressionDecision | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const [evalData, compData, regData] = await Promise.all([
          fetchBaselineEvaluation(),
          fetchExperimentComparison('chunk-400-50'),
          fetchRegressionDecision().catch(() => null),
        ])
        if (!active) return
        setEvaluation(evalData)
        setComparison(compData)
        setRegression(regData)
      } catch (err: unknown) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load evaluation dataset.')
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
      const [evalData, compData, regData] = await Promise.all([
        fetchBaselineEvaluation(),
        fetchExperimentComparison('chunk-400-50'),
        fetchRegressionDecision().catch(() => null),
      ])
      setEvaluation(evalData)
      setComparison(compData)
      setRegression(regData)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluation dataset.')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !evaluation) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <Skeleton height={90} />
        <Skeleton height={140} />
        <Skeleton height={240} />
      </div>
    )
  }

  if (error && !evaluation) {
    return <ErrorPanel title="Evaluation load error" message={error} onRetry={handleRetry} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Metric Strip & Metadata */}
      {evaluation && <EvaluationSummary evaluation={evaluation} />}

      {/* Baseline vs Candidate Comparison */}
      {comparison && <ComparisonView comparison={comparison} />}

      {/* Regression Policy Decision if present */}
      {regression && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: `1px solid ${
              regression.status === 'pass'
                ? 'var(--success-border)'
                : regression.status === 'fail'
                ? 'var(--error-border)'
                : 'var(--warning-border)'
            }`,
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 'var(--text-xs)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span
              style={{
                fontWeight: 700,
                color:
                  regression.status === 'pass'
                    ? 'var(--success)'
                    : regression.status === 'fail'
                    ? 'var(--error)'
                    : 'var(--warning)',
                textTransform: 'uppercase',
              }}
            >
              Regression Gate: {regression.status}
            </span>
            <span style={{ color: 'var(--text-secondary)' }}>{regression.summary}</span>
          </div>

          <span className="mono" style={{ color: 'var(--text-muted)' }}>
            {regression.checks.filter((c) => c.status === 'pass').length} passed / {regression.checks.length} checks
          </span>
        </div>
      )}

      {/* Detailed Query Table */}
      {evaluation && (
        <EvaluationTable queries={evaluation.queries} onSelectQuery={onInspectQuery} />
      )}
    </div>
  )
}
