import React, { useState } from 'react'
import { QueryInput } from '../components/query/QueryInput'
import { QueryTrace } from '../components/query/QueryTrace'
import { AnswerSection } from '../components/query/AnswerSection'
import { EvidenceList } from '../components/query/EvidenceList'
import { LatencyBreakdown } from '../components/query/LatencyBreakdown'
import { UsageCostSection } from '../components/query/UsageCostSection'
import { RequestDetails } from '../components/query/RequestDetails'
import { CodeBlock } from '../components/common/CodeBlock'
import { ErrorPanel } from '../components/common/ErrorPanel'
import { Skeleton } from '../components/common/Skeleton'
import { executeQuery } from '../api/query'
import type { RAGResponse } from '../types/rag'
import { MOCK_RAG_RESPONSE } from '../api/mockData'

export const QueryConsole: React.FC = () => {
  const [currentQuery, setCurrentQuery] = useState(
    'Which file formats does RAGBench V1 accept for ingestion?'
  )
  const [currentTopK, setCurrentTopK] = useState(5)
  const [response, setResponse] = useState<RAGResponse | null>(MOCK_RAG_RESPONSE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(
    null
  )
  const [showRawJson, setShowRawJson] = useState(false)

  const handleRunQuery = async (queryText: string, topK: number) => {
    setCurrentQuery(queryText)
    setCurrentTopK(topK)
    setLoading(true)
    setError(null)

    try {
      const res = await executeQuery({ query: queryText, top_k: topK })
      setResponse(res)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        const apiErr = err as { message: string; code?: string; requestId?: string }
        setError({
          message: apiErr.message,
          code: apiErr.code,
          requestId: apiErr.requestId,
        })
      } else {
        setError({
          message: 'An unexpected error occurred while executing the query.',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Query Input */}
      <QueryInput
        defaultQuery={currentQuery}
        defaultTopK={currentTopK}
        onRunQuery={handleRunQuery}
        loading={loading}
      />

      {/* Signature Execution Trace */}
      <QueryTrace query={currentQuery} response={response} loading={loading} />

      {error && (
        <ErrorPanel
          title="Query execution error"
          message={error.message}
          code={error.code}
          requestId={error.requestId}
          onRetry={() => handleRunQuery(currentQuery, currentTopK)}
        />
      )}

      {/* Two-Column Workspace Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.7fr) minmax(320px, 1fr)',
          gap: 'var(--space-4)',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Answer & Retrieved Evidence */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {loading ? (
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
              <Skeleton height={14} width={80} />
              <Skeleton height={20} width="90%" />
              <Skeleton height={20} width="75%" />
            </div>
          ) : (
            response && (
              <AnswerSection
                answer={response.answer}
                model={response.usage.model}
                requestId="req_query_live"
                isGrounded={response.sources.length > 0 && Boolean(response.usage.model)}
              />
            )
          )}

          {loading ? (
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
              }}
            >
              <Skeleton height={14} width={120} />
              <Skeleton height={42} />
              <Skeleton height={42} />
              <Skeleton height={42} />
            </div>
          ) : (
            response && <EvidenceList sources={response.sources} />
          )}
        </div>

        {/* Right Column: Latency, Usage, Metadata, Raw JSON */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {response && <LatencyBreakdown latency={response.latency} />}
          {response && <UsageCostSection usage={response.usage} />}
          <RequestDetails
            requestId="req_query_session"
            embeddingModel="sentence-transformers/all-MiniLM-L6-v2"
            generationModel={response?.usage.model || 'mock-llm'}
            topK={currentTopK}
            chunkSize={800}
            chunkOverlap={100}
          />

          {response && (
            <div>
              <button
                onClick={() => setShowRawJson(!showRawJson)}
                style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-muted)',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  marginBottom: showRawJson ? 'var(--space-2)' : 0,
                  display: 'block',
                }}
              >
                {showRawJson ? 'Hide raw response JSON' : 'Inspect raw response JSON'}
              </button>
              {showRawJson && (
                <CodeBlock
                  code={JSON.stringify(response, null, 2)}
                  title="RAGResponse"
                  maxHeight={360}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
