import React from 'react'
import { MetricStrip, type MetricItem } from '../common/MetricStrip'
import type { EvaluationResult } from '../../types/evaluation'

interface EvaluationSummaryProps {
  evaluation: EvaluationResult
}

export const EvaluationSummary: React.FC<EvaluationSummaryProps> = ({ evaluation }) => {
  const metrics: MetricItem[] = [
    { label: 'Recall@1', value: evaluation.metrics.recall_at_1, subtext: 'Exact top-1 match' },
    { label: 'Recall@3', value: evaluation.metrics.recall_at_3, subtext: 'In top-3 candidates' },
    { label: 'Recall@5', value: evaluation.metrics.recall_at_5, subtext: 'In top-5 candidates' },
    { label: 'MRR', value: evaluation.metrics.mrr, subtext: 'Mean reciprocal rank' },
  ]

  // If generation evaluation is present
  if (evaluation.generation_evaluation?.status === 'evaluated') {
    const gen = evaluation.generation_evaluation.aggregate_metrics
    if (gen.correctness !== undefined) {
      metrics.push({ label: 'Correctness', value: gen.correctness, subtext: 'Fact match' })
    }
    if (gen.faithfulness !== undefined) {
      metrics.push({ label: 'Faithfulness', value: gen.faithfulness, subtext: 'Context grounded' })
    }
    if (gen.context_relevance !== undefined) {
      metrics.push({ label: 'Context Rel.', value: gen.context_relevance, subtext: 'Evidence density' })
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {/* Header Info */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-primary)' }}>
            Evaluation Report
          </h2>
          <span
            className="mono"
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-secondary)',
              backgroundColor: 'var(--bg-surface-elevated)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            {evaluation.dataset_name} ({evaluation.dataset_version})
          </span>
        </div>

        <div className="mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {evaluation.query_count} queries | {Object.keys(evaluation.corpus_documents || {}).length} docs | fp: {evaluation.dataset_fingerprint.slice(0, 10)}...
        </div>
      </div>

      {/* Metric Strip */}
      <MetricStrip metrics={metrics} />
    </div>
  )
}
