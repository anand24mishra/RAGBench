import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ExperimentsPage } from '../pages/ExperimentsPage'
import { ExperimentInspectorPage } from '../pages/ExperimentInspectorPage'
import * as expApi from '../api/experiments'
import { MOCK_EXPERIMENTS, MOCK_EXPERIMENT_COMPARISON, MOCK_BASELINE_EVALUATION } from '../api/mockData'

describe('ExperimentsPage', () => {
  it('renders experiment table with all families', async () => {
    vi.spyOn(expApi, 'fetchExperiments').mockResolvedValueOnce(MOCK_EXPERIMENTS)

    const onSelectSpy = vi.fn()
    render(<ExperimentsPage onSelectExperiment={onSelectSpy} />)

    await waitFor(() => {
      expect(screen.getByText(/Controlled Retrieval Experiments/i)).toBeInTheDocument()
      expect(screen.getByText('chunk-400-50')).toBeInTheDocument()
      expect(screen.getByText('topk-1')).toBeInTheDocument()
      expect(screen.getByText('embed-paraphrase-minilm-l3-v2')).toBeInTheDocument()
    })
  })

  it('filters experiments by family', async () => {
    render(<ExperimentsPage onSelectExperiment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('chunk-400-50')).toBeInTheDocument()
    })

    const topKFilter = screen.getByRole('button', { name: /Top-K/i })
    fireEvent.click(topKFilter)

    expect(screen.getByText('topk-1')).toBeInTheDocument()
    expect(screen.queryByText('chunk-400-50')).not.toBeInTheDocument()
  })

  it('navigates to experiment inspector on row click', async () => {
    const onSelectSpy = vi.fn()
    render(<ExperimentsPage onSelectExperiment={onSelectSpy} />)

    await waitFor(() => {
      expect(screen.getByText('chunk-400-50')).toBeInTheDocument()
    })

    const row = screen.getByText('chunk-400-50').closest('tr')
    fireEvent.click(row!)

    expect(onSelectSpy).toHaveBeenCalledWith('chunk-400-50')
  })
})

describe('ExperimentInspectorPage', () => {
  it('renders configuration, metrics vs baseline, and ranking changes', async () => {
    vi.spyOn(expApi, 'fetchExperimentDetail').mockResolvedValue(MOCK_BASELINE_EVALUATION)
    vi.spyOn(expApi, 'fetchExperimentComparison').mockResolvedValue(MOCK_EXPERIMENT_COMPARISON)

    render(
      <ExperimentInspectorPage
        experimentId="chunk-400-50"
        onBack={vi.fn()}
        onInspectQuery={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getAllByText('chunk-400-50')[0]).toBeInTheDocument()
      expect(screen.getByText(/Experiment Configuration/i)).toBeInTheDocument()
      expect(screen.getByText(/Metrics vs Baseline/i)).toBeInTheDocument()
      expect(screen.getByText(/Ranking Change Analysis/i)).toBeInTheDocument()
      expect(screen.getByText(/rank 4/i)).toBeInTheDocument()
      expect(screen.getAllByText(/rank 1/i)[0]).toBeInTheDocument()
    })
  })
})
