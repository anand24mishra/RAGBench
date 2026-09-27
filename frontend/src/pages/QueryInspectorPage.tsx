import React, { useEffect, useState } from 'react'
import { ArrowLeft, Copy, Check, AlertCircle } from 'lucide-react'
import { Button } from '../components/common/Button'
import { Badge } from '../components/common/Badge'
import { MetricStrip, type MetricItem } from '../components/common/MetricStrip'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorPanel } from '../components/common/ErrorPanel'
import { fetchQueryInspection } from '../api/experiments'
import type { QueryEvaluationResult, RetrievedDocumentResult } from '../types/evaluation'
import { MOCK_BASELINE_EVALUATION } from '../api/mockData'

interface QueryInspectorPageProps {
  queryId: string
  onBack: () => void
}

export const QueryInspectorPage: React.FC<QueryInspectorPageProps> = ({ queryId, onBack }) => {
  const [data, setData] = useState<{
    query_id: string
    baseline_retrieval: QueryEvaluationResult | null
    generation_evaluation: QueryEvaluationResult | null
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copiedContext, setCopiedContext] = useState(false)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const res = await fetchQueryInspection(queryId)
        if (!active) return
        setData(res)
      } catch (err: unknown) {
        if (!active) return
        setError(err instanceof Error ? err.message : `Failed to inspect query ${queryId}`)
      }
    }
    load()
    return () => {
      active = false
    }
  }, [queryId])

  const handleRetry = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchQueryInspection(queryId)
      setData(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to inspect query ${queryId}`)
    } finally {
      setLoading(false)
    }
  }

  const queryRecord =
    data?.baseline_retrieval ||
    MOCK_BASELINE_EVALUATION.queries.find((q) => q.query_id === queryId) ||
    MOCK_BASELINE_EVALUATION.queries[0]

  const handleCopyContext = async () => {
    if (!queryRecord.context) return
    try {
      await navigator.clipboard.writeText(queryRecord.context)
      setCopiedContext(true)
      setTimeout(() => setCopiedContext(false), 1500)
    } catch {
      // ignore
    }
  }

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <Skeleton height={40} width={200} />
        <Skeleton height={140} />
        <Skeleton height={200} />
      </div>
    )
  }

  if (error && !data) {
    return <ErrorPanel title="Query inspection error" message={error} onRetry={handleRetry} />
  }

  const expectedDoc = queryRecord.relevant_documents?.[0]
  const targetItem = queryRecord.retrieved?.find((r: RetrievedDocumentResult) => r.document_id === expectedDoc)
  const targetRank = targetItem ? targetItem.rank : null

  const evalMetrics: MetricItem[] = [
    { label: 'Recall@1', value: queryRecord.recall_at_1 },
    { label: 'Recall@3', value: queryRecord.recall_at_3 },
    { label: 'Recall@5', value: queryRecord.recall_at_5 },
    { label: 'Reciprocal Rank', value: queryRecord.reciprocal_rank },
  ]

  if (queryRecord.generation_metrics) {
    evalMetrics.push({
      label: 'Correctness',
      value: queryRecord.generation_metrics.correctness,
      subtext: 'vs reference',
    })
    evalMetrics.push({
      label: 'Faithfulness',
      value: queryRecord.generation_metrics.faithfulness,
      subtext: 'vs context',
    })
    evalMetrics.push({
      label: 'Context Rel.',
      value: queryRecord.generation_metrics.context_relevance,
      subtext: 'evidence %',
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Header & Breadcrumb */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <Button variant="ghost" size="sm" onClick={onBack} icon={<ArrowLeft size={14} />}>
            Back
          </Button>
          <div style={{ height: 16, width: 1, backgroundColor: 'var(--border-medium)' }} />
          <h2 className="mono" style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text-primary)' }}>
            {queryRecord.query_id}
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
            Query Diagnostic Inspector
          </span>
        </div>
      </div>

      {/* Stage 1: Question & Expected Evidence */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        <div className="section-header">01 Question & Ground Truth Target</div>

        <div style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
          "{queryRecord.question}"
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginTop: 'var(--space-1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Target document:</span>
            <span
              className="mono"
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--accent-primary)',
                backgroundColor: 'var(--bg-base)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {expectedDoc || '—'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Actual retrieval rank:</span>
            <span
              className="mono"
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 700,
                color: targetRank === 1 ? 'var(--success)' : targetRank && targetRank <= 3 ? 'var(--text-primary)' : 'var(--error)',
              }}
            >
              {targetRank !== null ? `#${targetRank}` : 'NOT RETRIEVED IN TOP-K'}
            </span>
          </div>

          {targetRank !== null && targetRank > 1 && (
            <Badge variant="warning" size="sm">
              Suboptimal Rank #{targetRank}
            </Badge>
          )}
        </div>
      </div>

      {/* Stage 2: Ranked Evidence Retrieved */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        <div className="section-header">02 Retrieval Pipeline Ranking (Top-K)</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {queryRecord.retrieved?.map((item: RetrievedDocumentResult) => {
            const isTarget = item.document_id === expectedDoc
            return (
              <div
                key={item.chunk_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  backgroundColor: isTarget ? 'var(--bg-surface-elevated)' : 'var(--bg-base)',
                  border: `1px solid ${isTarget ? 'var(--accent-border)' : 'var(--border-subtle)'}`,
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-xs)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <span
                    className="mono"
                    style={{
                      fontWeight: 700,
                      color: item.rank === 1 ? 'var(--accent-primary)' : 'var(--text-muted)',
                      width: 24,
                    }}
                  >
                    #{item.rank}
                  </span>
                  <span
                    className="mono"
                    style={{
                      fontWeight: isTarget ? 700 : 500,
                      color: isTarget ? 'var(--text-primary)' : 'var(--text-secondary)',
                    }}
                  >
                    {item.document_id}
                  </span>
                  {isTarget && (
                    <Badge variant="success" size="sm">
                      Target Match
                    </Badge>
                  )}
                  <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                    chunk: {item.chunk_id.slice(0, 8)}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>score</span>
                  <span
                    className="mono"
                    style={{
                      fontWeight: 600,
                      color: item.score >= 0.7 ? 'var(--success)' : 'var(--text-primary)',
                    }}
                  >
                    {item.score.toFixed(4)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Stage 3: Assembled Context Payload */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            03 Assembled Context Payload (What the LLM received)
          </div>
          <button
            onClick={handleCopyContext}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontSize: '11px',
              color: copiedContext ? 'var(--success)' : 'var(--text-secondary)',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '2px 8px',
            }}
          >
            {copiedContext ? <Check size={11} /> : <Copy size={11} />}
            <span>{copiedContext ? 'Copied' : 'Copy context'}</span>
          </button>
        </div>

        <pre
          className="mono"
          style={{
            padding: 'var(--space-3)',
            backgroundColor: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap',
            maxHeight: 220,
            overflowY: 'auto',
            lineHeight: 1.5,
          }}
        >
          {queryRecord.context || 'Context payload was not recorded for this query snapshot.'}
        </pre>
      </div>

      {/* Stage 4: Generation Output & Reference */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        <div className="section-header">04 Generation Output & Ground Truth Reference</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
          <div>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>
              GENERATED ANSWER
            </div>
            <div
              style={{
                padding: 'var(--space-3)',
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-primary)',
                lineHeight: 1.5,
                minHeight: 80,
              }}
            >
              {queryRecord.generated_answer || 'No generation output captured.'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>
              REFERENCE GROUND TRUTH ANSWER
            </div>
            <div
              style={{
                padding: 'var(--space-3)',
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                minHeight: 80,
              }}
            >
              {queryRecord.reference_answer || 'No reference answer defined.'}
            </div>
          </div>
        </div>
      </div>

      {/* Stage 5: Evaluation & Failure Classification */}
      <div>
        <div className="section-header">05 Evaluation Metrics & Diagnostic Score</div>
        <MetricStrip metrics={evalMetrics} />
      </div>

      {queryRecord.failure_classification && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--warning-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
          }}
        >
          <AlertCircle size={16} color="var(--warning)" />
          <div style={{ fontSize: 'var(--text-xs)' }}>
            <span style={{ fontWeight: 600, color: 'var(--warning)', textTransform: 'uppercase' }}>
              Failure Classification:{' '}
            </span>
            <span className="mono" style={{ color: 'var(--text-primary)' }}>
              {queryRecord.failure_classification}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
