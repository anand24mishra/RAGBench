import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { EvaluationPage } from '../pages/EvaluationPage'
import * as evalApi from '../api/evaluation'
import { MOCK_BASELINE_EVALUATION } from '../api/mockData'

describe('EvaluationPage', () => {
  it('renders evaluation summary, metrics strip, and dataset metadata', async () => {
    vi.spyOn(evalApi, 'fetchBaselineEvaluation').mockResolvedValueOnce(MOCK_BASELINE_EVALUATION)

    const onInspectSpy = vi.fn()
    render(<EvaluationPage onInspectQuery={onInspectSpy} />)

    await waitFor(() => {
      expect(screen.getByText(/Evaluation Report/i)).toBeInTheDocument()
      expect(screen.getByText(/ragbench-v2-baseline/i)).toBeInTheDocument()
      expect(screen.getAllByText(/Recall@1/i)[0]).toBeInTheDocument()
      expect(screen.getAllByText(/Recall@5/i)[0]).toBeInTheDocument()
      expect(screen.getAllByText(/MRR/i)[0]).toBeInTheDocument()
    })
  })

  it('renders baseline vs candidate comparison with measured changes', async () => {
    render(<EvaluationPage onInspectQuery={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/Baseline vs Candidate Comparison/i)).toBeInTheDocument()
      expect(screen.getByText(/v2-baseline → chunk-400-50/i)).toBeInTheDocument()
      expect(screen.getByText(/Measured change/i)).toBeInTheDocument()
    })
  })

  it('renders per-query table and triggers inspection navigation on row click', async () => {
    const onInspectSpy = vi.fn()
    render(<EvaluationPage onInspectQuery={onInspectSpy} />)

    await waitFor(() => {
      expect(screen.getByText(/Per-Query Retrieval & Generation Results/i)).toBeInTheDocument()
      expect(screen.getByText('q001')).toBeInTheDocument()
      expect(screen.getByText('q007')).toBeInTheDocument()
    })

    const q007Row = screen.getByText('q007').closest('tr')
    expect(q007Row).not.toBeNull()
    fireEvent.click(q007Row!)

    expect(onInspectSpy).toHaveBeenCalledWith('q007')
  })
})
