import React, { useEffect, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { Button } from '../components/common/Button'
import { MetricStrip, type MetricItem } from '../components/common/MetricStrip'
import { KeyValueGrid } from '../components/common/KeyValueGrid'
import { RankingChangeList } from '../components/experiments/RankingChangeList'
import { CodeBlock } from '../components/common/CodeBlock'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorPanel } from '../components/common/ErrorPanel'
import { fetchExperimentDetail, fetchExperimentComparison } from '../api/experiments'
import type { EvaluationResult, ComparisonResult } from '../types/evaluation'
import { MOCK_BASELINE_EVALUATION, MOCK_EXPERIMENT_COMPARISON } from '../api/mockData'

interface ExperimentInspectorPageProps {
  experimentId: string
  onBack: () => void
  onInspectQuery?: (queryId: string) => void
}

export const ExperimentInspectorPage: React.FC<ExperimentInspectorPageProps> = ({
  experimentId,
  onBack,
  onInspectQuery,
}) => {
  const [detail, setDetail] = useState<EvaluationResult | null>(MOCK_BASELINE_EVALUATION)
  const [comparison, setComparison] = useState<ComparisonResult | null>(MOCK_EXPERIMENT_COMPARISON)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const [expData, compData] = await Promise.all([
          fetchExperimentDetail(experimentId),
          fetchExperimentComparison(experimentId).catch(() => null),
        ])
        if (!active) return
        setDetail(expData)
        setComparison(compData)
      } catch (err: unknown) {
        if (!active) return
        setError(err instanceof Error ? err.message : `Failed to load experiment ${experimentId}`)
      }
    }
    load()
    return () => {
      active = false
    }
  }, [experimentId])

  const handleRetry = async () => {
    setLoading(true)
    setError(null)
    try {
      const [expData, compData] = await Promise.all([
        fetchExperimentDetail(experimentId),
        fetchExperimentComparison(experimentId).catch(() => null),
      ])
      setDetail(expData)
      setComparison(compData)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to load experiment ${experimentId}`)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !detail) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <Skeleton height={40} width={200} />
        <Skeleton height={120} />
        <Skeleton height={200} />
      </div>
    )
  }

  if (error && !detail) {
    return <ErrorPanel title="Experiment load failure" message={error} onRetry={handleRetry} />
  }

  const metrics: MetricItem[] = detail
    ? [
        {
          label: 'Recall@1',
          value: detail.metrics.recall_at_1,
          delta: comparison?.metric_differences?.recall_at_1,
        },
        {
          label: 'Recall@3',
          value: detail.metrics.recall_at_3,
          delta: comparison?.metric_differences?.recall_at_3,
        },
        {
          label: 'Recall@5',
          value: detail.metrics.recall_at_5,
          delta: comparison?.metric_differences?.recall_at_5,
        },
        {
          label: 'MRR',
          value: detail.metrics.mrr,
          delta: comparison?.metric_differences?.mrr,
        },
      ]
    : []

  const configItems = detail
    ? [
        { key: 'Experiment ID', value: detail.experiment_id, mono: true },
        { key: 'Dataset version', value: detail.dataset_version, mono: true },
        { key: 'Chunk size', value: `${detail.retriever_configuration.chunk_size} chars`, mono: true },
        { key: 'Chunk overlap', value: `${detail.retriever_configuration.chunk_overlap} chars`, mono: true },
        { key: 'Top K candidates', value: String(detail.top_k), mono: true },
        { key: 'Embedding model', value: detail.embedding_model.split('/').pop() || detail.embedding_model, mono: true },
        { key: 'Vector store', value: `${detail.retriever_configuration.vector_store} (${detail.retriever_configuration.distance})`, mono: true },
        { key: 'Dataset fingerprint', value: `${detail.dataset_fingerprint.slice(0, 16)}...`, mono: true },
      ]
    : []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <Button variant="ghost" size="sm" onClick={onBack} icon={<ArrowLeft size={14} />}>
            Back to experiments
          </Button>
          <div style={{ height: 16, width: 1, backgroundColor: 'var(--border-medium)' }} />
          <h2 className="mono" style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text-primary)' }}>
            {experimentId}
          </h2>
          <span
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              backgroundColor: 'var(--bg-surface-elevated)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            Controlled Experiment Report
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div>
        <div className="section-header">Metrics vs Baseline</div>
        <MetricStrip metrics={metrics} />
      </div>

      {/* Configuration Grid */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
        }}
      >
        <div className="section-header">Experiment Configuration</div>
        <KeyValueGrid items={configItems} columns={2} />
      </div>

      {/* Performance Latency Percentiles if available */}
      {detail?.timing && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
          }}
        >
          <div className="section-header">Stage Latency Percentiles (Steady-State)</div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: 'var(--space-3)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <div style={{ backgroundColor: 'var(--bg-base)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)' }}>Mean Latency</div>
              <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {detail.timing.mean_ms ? `${detail.timing.mean_ms.toFixed(2)} ms` : '—'}
              </div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-base)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)' }}>p50 (Median)</div>
              <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {detail.timing.p50_ms ? `${detail.timing.p50_ms.toFixed(2)} ms` : '—'}
              </div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-base)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)' }}>p95 (Tail)</div>
              <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {detail.timing.p95_ms ? `${detail.timing.p95_ms.toFixed(2)} ms` : '—'}
              </div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-base)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)' }}>p99 (Outlier)</div>
              <div className="mono" style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                {detail.timing.p99_ms ? `${detail.timing.p99_ms.toFixed(2)} ms` : '—'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Signature Ranking Changes */}
      {comparison?.ranking_changes && (
        <RankingChangeList
          rankingChanges={comparison.ranking_changes}
          onInspectQuery={onInspectQuery}
        />
      )}

      {/* Raw JSON toggle */}
      {detail && (
        <div>
          <button
            onClick={() => setShowRaw(!showRaw)}
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              textDecoration: 'underline',
              cursor: 'pointer',
              marginBottom: showRaw ? 'var(--space-2)' : 0,
            }}
          >
            {showRaw ? 'Hide raw experiment JSON' : 'Inspect raw experiment JSON'}
          </button>
          {showRaw && <CodeBlock code={JSON.stringify(detail, null, 2)} title={detail.experiment_id} />}
        </div>
      )}
    </div>
  )
}
