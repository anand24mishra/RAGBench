from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from evaluation.models import (
    GenerationFailureType,
    GenerationMetrics,
)
from ragbench.app.generation.base import LLMProvider

logger = logging.getLogger("ragbench.evaluation.generation")

STOP_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


@dataclass(frozen=True)
class GenerationEvaluationResult:
    metrics: GenerationMetrics
    details: dict[str, Any]
    failure_classification: GenerationFailureType | None = None
    reason: str | None = None


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and standardizing whitespace."""
    return " ".join(text.lower().split())


def extract_content_tokens(text: str) -> list[str]:
    """Extract content words and alphanumeric tokens, filtering stopwords."""
    raw_tokens = re.findall(r"[a-z0-9_\-]+", text.lower())
    clean_tokens = [t.strip(".-_") for t in raw_tokens if t.strip(".-_")]
    content = [t for t in clean_tokens if len(t) > 1 and t not in STOP_WORDS]
    return content or clean_tokens


def split_claims(text: str) -> list[str]:
    """Split generated text into individual claim-bearing sentences/clauses."""
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    claims: list[str] = []
    for s in raw_sentences:
        clean = s.strip()
        if len(clean) > 3:
            claims.append(clean)
    return claims


def is_fact_satisfied(fact: str, answer: str) -> bool:
    """
    Check if a required fact is satisfied in the answer.

    Evaluates via:
    1. Normalized exact substring matching
    2. High-overlap content token containment (>= 80% coverage)
    """
    norm_fact = normalize_text(fact)
    norm_answer = normalize_text(answer)
    if not norm_fact or not norm_answer:
        return False

    if norm_fact in norm_answer:
        return True

    fact_tokens = extract_content_tokens(fact)
    if not fact_tokens:
        return False

    answer_tokens = set(extract_content_tokens(answer))
    matched = sum(1 for tok in fact_tokens if tok in answer_tokens)
    return (matched / len(fact_tokens)) >= 0.8


class GenerationEvaluator(ABC):
    """Abstract evaluator for generation quality."""

    evaluator_type: str = "base"

    @abstractmethod
    async def evaluate(
        self,
        question: str,
        retrieved_context: str,
        generated_answer: str,
        reference_answer: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> GenerationEvaluationResult:
        """Evaluate generation quality across correctness, faithfulness, and context relevance."""


class DeterministicGenerationEvaluator(GenerationEvaluator):
    """
    Rule-based, transparent generation evaluator.

    Metrics:
    - correctness: fraction of required facts satisfied in the answer
    - faithfulness: fraction of claims in the answer supported by retrieved evidence
    - context_relevance: proportion of relevant evidence present in retrieved context
    """

    evaluator_type: str = "deterministic"

    def __init__(
        self,
        *,
        correctness_threshold: float = 0.7,
        faithfulness_threshold: float = 0.7,
        context_relevance_threshold: float = 0.25,
    ) -> None:
        self.correctness_threshold = correctness_threshold
        self.faithfulness_threshold = faithfulness_threshold
        self.context_relevance_threshold = context_relevance_threshold

    async def evaluate(
        self,
        question: str,
        retrieved_context: str,
        generated_answer: str,
        reference_answer: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> GenerationEvaluationResult:
        meta = metadata or {}
        required_facts: list[str] = meta.get("required_facts", [])
        relevant_documents: list[str] = meta.get("relevant_documents", [])
        retrieved_documents: list[str] = meta.get("retrieved_documents", [])

        # 1. Answer Correctness
        correctness, satisfied_facts, missing_facts = self._evaluate_correctness(
            generated_answer, reference_answer, required_facts
        )

        # 2. Faithfulness / Groundedness
        faithfulness, supported_claims, unsupported_claims = self._evaluate_faithfulness(
            generated_answer, retrieved_context
        )

        # 3. Context Relevance
        context_relevance, context_details = self._evaluate_context_relevance(
            relevant_documents, retrieved_documents
        )

        # 4. Failure Classification
        failure_type: GenerationFailureType | None = None
        reason: str | None = None

        if not retrieved_documents or not any(d in relevant_documents for d in retrieved_documents):
            failure_type = "retrieval_failure"
            reason = f"No expected documents {relevant_documents} present in retrieved candidates"
        elif context_relevance < self.context_relevance_threshold:
            failure_type = "context_failure"
            reason = (
                f"Context relevance {context_relevance:.2f} below threshold "
                f"{self.context_relevance_threshold:.2f}"
            )
        elif not generated_answer.strip():
            failure_type = "generation_failure"
            reason = "Generated answer is empty"
        elif faithfulness < self.faithfulness_threshold:
            failure_type = "grounding_failure"
            reason = (
                f"Faithfulness {faithfulness:.2f} < {self.faithfulness_threshold:.2f}; "
                f"unsupported claims: {unsupported_claims}"
            )
        elif correctness < self.correctness_threshold:
            failure_type = "generation_failure"
            reason = (
                f"Correctness {correctness:.2f} below threshold {self.correctness_threshold:.2f}; "
                f"missing required facts: {missing_facts}"
            )

        metrics = GenerationMetrics(
            correctness=round(correctness, 6),
            faithfulness=round(faithfulness, 6),
            context_relevance=round(context_relevance, 6),
        )
        details = {
            "satisfied_facts": satisfied_facts,
            "missing_facts": missing_facts,
            "supported_claims": supported_claims,
            "unsupported_claims": unsupported_claims,
            "context_details": context_details,
        }

        return GenerationEvaluationResult(
            metrics=metrics,
            details=details,
            failure_classification=failure_type,
            reason=reason,
        )

    def _evaluate_correctness(
        self,
        answer: str,
        reference: str | None,
        required_facts: list[str],
    ) -> tuple[float, list[str], list[str]]:
        clean_answer = answer.strip()
        if not clean_answer:
            return 0.0, [], required_facts

        # Check for explicit insufficiency answer
        is_insufficient_answer = "insufficient" in clean_answer.lower()

        if required_facts:
            satisfied: list[str] = []
            missing: list[str] = []
            for fact in required_facts:
                if is_fact_satisfied(fact, clean_answer):
                    satisfied.append(fact)
                else:
                    missing.append(fact)
            score = len(satisfied) / len(required_facts)
            return score, satisfied, missing

        if reference:
            ref_tokens = set(extract_content_tokens(reference))
            if not ref_tokens:
                return (1.0 if not is_insufficient_answer else 0.0), [], []
            ans_tokens = set(extract_content_tokens(clean_answer))
            matched = len(ref_tokens & ans_tokens)
            score = matched / len(ref_tokens)
            return score, list(ref_tokens & ans_tokens), list(ref_tokens - ans_tokens)

        return 1.0, [], []

    def _evaluate_faithfulness(
        self,
        answer: str,
        context: str,
    ) -> tuple[float, list[str], list[str]]:
        claims = split_claims(answer)
        if not claims:
            return 0.0, [], ["Empty answer"]

        clean_context = context.strip()
        is_empty_context = not clean_context

        supported: list[str] = []
        unsupported: list[str] = []

        context_tokens = set(extract_content_tokens(clean_context))

        for claim in claims:
            # If the model explicitly indicates insufficient context:
            if "insufficient" in claim.lower() and (
                "context" in claim.lower() or "available" in claim.lower()
            ):
                supported.append(claim)
                continue

            if is_empty_context:
                unsupported.append(claim)
                continue

            claim_tokens = extract_content_tokens(claim)
            if not claim_tokens:
                supported.append(claim)
                continue

            matched = sum(1 for tok in claim_tokens if tok in context_tokens)
            overlap = matched / len(claim_tokens)
            # A claim is supported if >= 70% of its content tokens appear in the retrieved context
            if overlap >= 0.70:
                supported.append(claim)
            else:
                unsupported.append(claim)

        faithfulness = len(supported) / len(claims)
        return faithfulness, supported, unsupported

    def _evaluate_context_relevance(
        self,
        relevant_documents: list[str],
        retrieved_documents: list[str],
    ) -> tuple[float, dict[str, Any]]:
        if not retrieved_documents:
            return 0.0, {"hit_rank_1": False, "relevant_chunk_ratio": 0.0}

        relevant_set = set(relevant_documents)
        hit_rank_1 = retrieved_documents[0] in relevant_set
        relevant_chunk_count = sum(1 for d in retrieved_documents if d in relevant_set)
        total_retrieved = len(retrieved_documents)
        ratio = relevant_chunk_count / total_retrieved

        # Relevance score combines top-1 hit (50% weight) and relevant chunk ratio (50% weight)
        relevance = 0.5 * (1.0 if hit_rank_1 else 0.0) + 0.5 * ratio

        details = {
            "hit_rank_1": hit_rank_1,
            "relevant_chunk_count": relevant_chunk_count,
            "total_retrieved": total_retrieved,
            "relevant_chunk_ratio": round(ratio, 4),
        }
        return relevance, details


class LLMJudgeGenerationEvaluator(GenerationEvaluator):
    """
    LLM-as-a-judge generation evaluator using structured JSON output.

    Requests ratings for correctness, faithfulness, and context relevance on [0.0, 1.0].
    Validates output schema and handles provider timeouts or malformed responses.
    """

    evaluator_type: str = "llm_judge"

    JUDGE_SYSTEM_PROMPT = """You are an objective evaluation judge for a RAG system.
Evaluate the candidate answer against the question, retrieved context, and reference answer.
Output ONLY a valid JSON object with the following exact keys:
{
  "correctness": <float between 0.0 and 1.0>,
  "faithfulness": <float between 0.0 and 1.0>,
  "context_relevance": <float between 0.0 and 1.0>,
  "reason": "<short explanation>"
}
Definitions:
- correctness: How accurately does the answer match reference facts? (0.0=wrong, 1.0=correct)
- faithfulness: Are claims supported by retrieved context? (0.0=hallucinated, 1.0=grounded)
- context_relevance: Does context contain evidence to answer? (0.0=irrelevant, 1.0=relevant)
Do not output Markdown backticks or any surrounding text, ONLY the JSON string."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        *,
        judge_model: str = "llm-judge",
        judge_prompt_version: str = "1.0",
        temperature: float = 0.0,
    ) -> None:
        self.llm_provider = llm_provider
        self.judge_model = judge_model
        self.judge_prompt_version = judge_prompt_version
        self.temperature = temperature

    async def evaluate(
        self,
        question: str,
        retrieved_context: str,
        generated_answer: str,
        reference_answer: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> GenerationEvaluationResult:
        meta = metadata or {}
        required_facts = meta.get("required_facts", [])

        user_prompt = (
            f"Question: {question}\n\n"
            f"Retrieved Context:\n{retrieved_context}\n\n"
            f"Generated Answer:\n{generated_answer}\n\n"
            f"Reference Answer:\n{reference_answer or 'None provided'}\n\n"
            f"Required Facts:\n{json.dumps(required_facts)}\n"
        )

        try:
            res = await self.llm_provider.generate(
                user_prompt, system_prompt=self.JUDGE_SYSTEM_PROMPT
            )
            raw_text = res.text.strip()
            # Clean possible markdown wrapping if the LLM output markdown fences
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)
            data = json.loads(raw_text)

            correctness = float(data["correctness"])
            faithfulness = float(data["faithfulness"])
            context_relevance = float(data["context_relevance"])
            reason = str(data.get("reason", ""))

            # Clamp scores to [0.0, 1.0]
            correctness = max(0.0, min(1.0, correctness))
            faithfulness = max(0.0, min(1.0, faithfulness))
            context_relevance = max(0.0, min(1.0, context_relevance))

            failure_type: GenerationFailureType | None = None
            if correctness < 0.7:
                failure_type = "generation_failure"
            elif faithfulness < 0.7:
                failure_type = "grounding_failure"
            elif context_relevance < 0.25:
                failure_type = "context_failure"

            metrics = GenerationMetrics(
                correctness=round(correctness, 6),
                faithfulness=round(faithfulness, 6),
                context_relevance=round(context_relevance, 6),
            )
            return GenerationEvaluationResult(
                metrics=metrics,
                details={
                    "judge_model": self.judge_model,
                    "judge_prompt_version": self.judge_prompt_version,
                    "reason": reason,
                    "raw_response": raw_text,
                },
                failure_classification=failure_type,
                reason=reason,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("LLM judge returned malformed response: %s", exc)
            return GenerationEvaluationResult(
                metrics=GenerationMetrics(correctness=0.0, faithfulness=0.0, context_relevance=0.0),
                details={
                    "judge_model": self.judge_model,
                    "judge_prompt_version": self.judge_prompt_version,
                    "error": f"Malformed judge response: {exc}",
                },
                failure_classification="provider_failure",
                reason=f"Malformed judge response: {exc}",
            )
        except Exception as exc:
            logger.error("LLM judge evaluation failed: %s", exc)
            return GenerationEvaluationResult(
                metrics=GenerationMetrics(correctness=0.0, faithfulness=0.0, context_relevance=0.0),
                details={
                    "judge_model": self.judge_model,
                    "judge_prompt_version": self.judge_prompt_version,
                    "error": str(exc),
                },
                failure_classification="provider_failure",
                reason=f"Judge provider error: {exc}",
            )
