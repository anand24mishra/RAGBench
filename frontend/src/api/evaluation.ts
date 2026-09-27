import { requestJson } from './client'
import type { EvaluationResult, RegressionDecision } from '../types/evaluation'
import { MOCK_BASELINE_EVALUATION, MOCK_REGRESSION_DECISION } from './mockData'

export async function fetchBaselineEvaluation(): Promise<EvaluationResult> {
  return requestJson<EvaluationResult>('/evaluation/baseline', {}, MOCK_BASELINE_EVALUATION)
}

export async function fetchGenerationBaseline(): Promise<EvaluationResult> {
  return requestJson<EvaluationResult>('/evaluation/generation-baseline', {}, MOCK_BASELINE_EVALUATION)
}

export async function fetchCandidateEvaluation(): Promise<EvaluationResult> {
  return requestJson<EvaluationResult>('/evaluation/candidate', {}, MOCK_BASELINE_EVALUATION)
}

export async function fetchRegressionDecision(): Promise<RegressionDecision> {
  return requestJson<RegressionDecision>('/evaluation/regression', {}, MOCK_REGRESSION_DECISION)
}
