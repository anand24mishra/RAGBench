# RAGBench Regression Gate Report: FAILED

- **Status**: `fail`
- **Baseline ID**: `generation-v4-baseline`
- **Candidate ID**: `generation-v4-baseline`
- **Dataset Version**: `1.1.0`
- **Summary**: Regression check FAIL: 8 passed, 2 failed, 1 inconclusive. Regressed queries: 0.

## Regression Checks

| Category | Metric | Baseline | Candidate | Delta | Threshold | Status |
|---|---|---|---|---|---|---|
| quality | `recall_at_1` | 0.857143 | 0.857143 | +0.0000 | -0.05 | **PASS** |
| quality | `recall_at_3` | 0.964286 | 0.964286 | +0.0000 | -0.05 | **PASS** |
| quality | `recall_at_5` | 1.0 | 1.0 | +0.0000 | -0.02 | **PASS** |
| quality | `mrr` | 0.907738 | 0.907738 | +0.0000 | -0.02 | **PASS** |
| quality | `correctness` | 0.744048 | 0.744048 | +0.0000 | -0.05 | **PASS** |
| quality | `faithfulness` | 1.0 | 1.0 | +0.0000 | -0.05 | **PASS** |
| quality | `context_relevance` | 0.528571 | 0.528571 | +0.0000 | -0.05 | **PASS** |
| latency | `retrieval_p95_ms` | 0.501 | 0.688 | +0.1870 | 0.25 | **FAIL** |
| cost | `cost_per_query` | - | - | - | - | **INCONCLUSIVE** |
| reliability | `failure_rate` | - | 0.4643 | - | 0.05 | **FAIL** |
| reliability | `timeouts` | - | 0.0 | - | 0.0 | **PASS** |

