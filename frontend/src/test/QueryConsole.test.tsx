import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryConsole } from '../pages/QueryConsole'
import * as queryApi from '../api/query'
import { MOCK_RAG_RESPONSE } from '../api/mockData'

describe('QueryConsole', () => {
  it('renders query input, default parameters, and initial response', () => {
    render(<QueryConsole />)

    expect(screen.getByLabelText(/Query/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run Query/i })).toBeInTheDocument()
    expect(screen.getByText(/Pipeline Execution Trace/i)).toBeInTheDocument()
    expect(screen.getByText(/^Answer$/i)).toBeInTheDocument()
    expect(screen.getByText(/Retrieved Evidence/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Latency/i)[0]).toBeInTheDocument()
    expect(screen.getByText(/Usage & Cost/i)).toBeInTheDocument()
    expect(screen.getByText(/Request Details/i)).toBeInTheDocument()
  })

  it('submits a new query and updates rendered answer and sources', async () => {
    const executeSpy = vi.spyOn(queryApi, 'executeQuery').mockResolvedValueOnce({
      ...MOCK_RAG_RESPONSE,
      answer: 'New custom answer tested from query console',
    })

    render(<QueryConsole />)

    const textarea = screen.getByLabelText(/Query/i)
    fireEvent.change(textarea, { target: { value: 'What is vector indexing?' } })

    const runBtn = screen.getByRole('button', { name: /Run Query/i })
    fireEvent.click(runBtn)

    await waitFor(() => {
      expect(executeSpy).toHaveBeenCalledWith({
        query: 'What is vector indexing?',
        top_k: 5,
      })
      expect(screen.getByText(/New custom answer tested from query console/i)).toBeInTheDocument()
    })
  })

  it('displays error panel on query execution failure with retry capability', async () => {
    vi.spyOn(queryApi, 'executeQuery').mockRejectedValueOnce(
      new Error('LLM connection timed out after 15000ms')
    )

    render(<QueryConsole />)

    const runBtn = screen.getByRole('button', { name: /Run Query/i })
    fireEvent.click(runBtn)

    await waitFor(() => {
      expect(screen.getByText(/Query execution error/i)).toBeInTheDocument()
      expect(screen.getByText(/LLM connection timed out/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Retry Request/i })).toBeInTheDocument()
    })
  })

  it('renders explicit unmeasured cost and token counts', () => {
    render(<QueryConsole />)

    expect(screen.getByText(/Input tokens/i)).toBeInTheDocument()
    expect(screen.getByText('384')).toBeInTheDocument()
    expect(screen.getByText(/Output tokens/i)).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText(/Total tokens/i)).toBeInTheDocument()
    expect(screen.getByText('426')).toBeInTheDocument()
    expect(screen.getByText(/Not measured/i)).toBeInTheDocument()
  })
})
