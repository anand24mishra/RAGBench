import { requestJson } from './client'
import type { ComparisonResult, EvaluationResult, QueryEvaluationResult } from '../types/evaluation'
import type { ExperimentSummary, SystemConfig } from '../types/experiments'
import {
  MOCK_BASELINE_EVALUATION,
  MOCK_EXPERIMENT_COMPARISON,
  MOCK_EXPERIMENTS,
  MOCK_SYSTEM_CONFIG,
} from './mockData'

export async function fetchExperiments(): Promise<ExperimentSummary[]> {
  return requestJson<ExperimentSummary[]>('/experiments', {}, MOCK_EXPERIMENTS)
}

export async function fetchExperimentDetail(experimentId: string): Promise<EvaluationResult> {
  return requestJson<EvaluationResult>(
    `/experiments/${encodeURIComponent(experimentId)}`,
    {},
    MOCK_BASELINE_EVALUATION
  )
}

export async function fetchExperimentComparison(experimentId: string): Promise<ComparisonResult> {
  return requestJson<ComparisonResult>(
    `/experiments/${encodeURIComponent(experimentId)}/comparison`,
    {},
    MOCK_EXPERIMENT_COMPARISON
  )
}

export async function fetchQueryInspection(
  queryId: string
): Promise<{ query_id: string; baseline_retrieval: QueryEvaluationResult | null; generation_evaluation: QueryEvaluationResult | null }> {
  const defaultQuery = MOCK_BASELINE_EVALUATION.queries.find((q) => q.query_id === queryId) || MOCK_BASELINE_EVALUATION.queries[0]
  return requestJson(
    `/inspect/${encodeURIComponent(queryId)}`,
    {},
    {
      query_id: queryId,
      baseline_retrieval: defaultQuery,
      generation_evaluation: defaultQuery,
    }
  )
}

export async function fetchSystemConfig(): Promise<SystemConfig> {
  return requestJson<SystemConfig>('/system/config', {}, MOCK_SYSTEM_CONFIG)
}
