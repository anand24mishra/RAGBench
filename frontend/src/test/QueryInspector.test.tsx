import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryInspectorPage } from '../pages/QueryInspectorPage'
import * as expApi from '../api/experiments'
import { MOCK_BASELINE_EVALUATION } from '../api/mockData'

describe('QueryInspectorPage', () => {
  it('renders reasoning stages: Question, Retrieval, Context, Generation, Evaluation', async () => {
    const q007 = MOCK_BASELINE_EVALUATION.queries.find((q) => q.query_id === 'q007')!
    vi.spyOn(expApi, 'fetchQueryInspection').mockResolvedValueOnce({
      query_id: 'q007',
      baseline_retrieval: q007,
      generation_evaluation: q007,
    })

    const onBackSpy = vi.fn()
    render(<QueryInspectorPage queryId="q007" onBack={onBackSpy} />)

    await waitFor(() => {
      expect(screen.getByText('q007')).toBeInTheDocument()
      expect(screen.getByText(/01 Question & Ground Truth Target/i)).toBeInTheDocument()
      expect(screen.getByText(/02 Retrieval Pipeline Ranking/i)).toBeInTheDocument()
      expect(screen.getByText(/03 Assembled Context Payload/i)).toBeInTheDocument()
      expect(screen.getByText(/04 Generation Output & Ground Truth Reference/i)).toBeInTheDocument()
      expect(screen.getByText(/05 Evaluation Metrics & Diagnostic Score/i)).toBeInTheDocument()
      expect(screen.getByText(/Suboptimal Rank #4/i)).toBeInTheDocument()
    })
  })
})
