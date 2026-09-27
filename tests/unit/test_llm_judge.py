import json

import pytest

from evaluation.generation_evaluator import LLMJudgeGenerationEvaluator
from ragbench.app.domain.errors import LLMProviderError, LLMTimeoutError
from ragbench.app.generation.base import GenerationResult, LLMProvider


class MockJudgeLLM(LLMProvider):
    def __init__(self, response_text: str | Exception) -> None:
        self.response = response_text

    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult:
        if isinstance(self.response, Exception):
            raise self.response
        return GenerationResult(
            text=self.response,
            model="mock-judge",
            input_tokens=100,
            output_tokens=25,
        )


@pytest.mark.asyncio
async def test_llm_judge_valid_response() -> None:
    judge_json = json.dumps(
        {
            "correctness": 0.95,
            "faithfulness": 1.0,
            "context_relevance": 0.85,
            "reason": "All facts satisfied and grounded.",
        }
    )
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM(judge_json), judge_model="test-judge")

    res = await judge.evaluate(
        question="What formats?",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 0.95
    assert res.metrics.faithfulness == 1.0
    assert res.metrics.context_relevance == 0.85
    assert res.failure_classification is None
    assert res.details["judge_model"] == "test-judge"
    assert res.details["reason"] == "All facts satisfied and grounded."


@pytest.mark.asyncio
async def test_llm_judge_markdown_fenced_json() -> None:
    fenced = (
        "```json\n"
        "{\n"
        '  "correctness": 0.8,\n'
        '  "faithfulness": 0.9,\n'
        '  "context_relevance": 0.7,\n'
        '  "reason": "Good"\n'
        "}\n"
        "```"
    )
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM(fenced))
    res = await judge.evaluate(
        question="What formats?",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 0.8
    assert res.metrics.faithfulness == 0.9
    assert res.metrics.context_relevance == 0.7


@pytest.mark.asyncio
async def test_llm_judge_score_clamping() -> None:
    out_of_bounds = json.dumps(
        {
            "correctness": 1.5,
            "faithfulness": -0.2,
            "context_relevance": 0.5,
            "reason": "Extreme scores",
        }
    )
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM(out_of_bounds))
    res = await judge.evaluate(
        question="Question",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 1.0
    assert res.metrics.faithfulness == 0.0
    assert res.metrics.context_relevance == 0.5


@pytest.mark.asyncio
async def test_llm_judge_malformed_json() -> None:
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM("This is not JSON at all!"))
    res = await judge.evaluate(
        question="Question",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 0.0
    assert res.metrics.faithfulness == 0.0
    assert res.metrics.context_relevance == 0.0
    assert res.failure_classification == "provider_failure"
    assert "Malformed judge response" in res.details["error"]


@pytest.mark.asyncio
async def test_llm_judge_timeout() -> None:
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM(LLMTimeoutError("Request timed out")))
    res = await judge.evaluate(
        question="Question",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 0.0
    assert res.failure_classification == "provider_failure"
    assert "Request timed out" in res.details["error"]


@pytest.mark.asyncio
async def test_llm_judge_provider_failure() -> None:
    judge = LLMJudgeGenerationEvaluator(MockJudgeLLM(LLMProviderError("500 Internal Server Error")))
    res = await judge.evaluate(
        question="Question",
        retrieved_context="Context",
        generated_answer="Answer",
        reference_answer="Ref",
    )

    assert res.metrics.correctness == 0.0
    assert res.failure_classification == "provider_failure"
    assert "500 Internal Server Error" in res.details["error"]
