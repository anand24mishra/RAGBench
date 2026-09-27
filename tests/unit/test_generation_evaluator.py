import pytest

from evaluation.generation_evaluator import (
    DeterministicGenerationEvaluator,
    is_fact_satisfied,
    split_claims,
)


@pytest.fixture
def evaluator() -> DeterministicGenerationEvaluator:
    return DeterministicGenerationEvaluator(
        correctness_threshold=0.7,
        faithfulness_threshold=0.7,
        context_relevance_threshold=0.25,
    )


# --- Fact Matching Tests ---


def test_is_fact_satisfied_exact() -> None:
    fact = "UTF-8 plain-text"
    answer = "RAGBench V1 accepts UTF-8 plain-text and Markdown files."
    assert is_fact_satisfied(fact, answer) is True


def test_is_fact_satisfied_case_insensitive() -> None:
    fact = "sha-256 digest"
    answer = "Calculated using the SHA-256 DIGEST of original bytes."
    assert is_fact_satisfied(fact, answer) is True


def test_is_fact_satisfied_token_overlap() -> None:
    fact = "dense top-k retrieval without hybrid search"
    answer = (
        "The system implements dense top-k retrieval and "
        "operates without hybrid search or reranking."
    )
    assert is_fact_satisfied(fact, answer) is True


def test_is_fact_satisfied_missing() -> None:
    fact = "BM25 keyword search"
    answer = "RAGBench V1 uses dense semantic retrieval with Qdrant."
    assert is_fact_satisfied(fact, answer) is False


def test_split_claims() -> None:
    text = "First claim about ingestion. Second claim about chunking! Third claim about retrieval?"
    claims = split_claims(text)
    assert len(claims) == 3
    assert claims[0] == "First claim about ingestion."
    assert claims[1] == "Second claim about chunking!"
    assert claims[2] == "Third claim about retrieval?"


# --- Correctness Tests ---


@pytest.mark.asyncio
async def test_correctness_exact_facts(evaluator: DeterministicGenerationEvaluator) -> None:
    res = await evaluator.evaluate(
        question="What chunk size and overlap are used?",
        retrieved_context="The baseline uses 800-character chunks with 100 characters of overlap.",
        generated_answer="The system uses 800-character chunks and 100 characters of overlap.",
        reference_answer="800-character chunks with 100 characters of overlap.",
        metadata={
            "required_facts": ["800-character chunks", "100 characters of overlap"],
            "relevant_documents": ["chunking"],
            "retrieved_documents": ["chunking"],
        },
    )
    assert res.metrics.correctness == 1.0
    assert len(res.details["missing_facts"]) == 0
    assert len(res.details["satisfied_facts"]) == 2


@pytest.mark.asyncio
async def test_correctness_partial_facts(evaluator: DeterministicGenerationEvaluator) -> None:
    res = await evaluator.evaluate(
        question="What chunk size and overlap are used?",
        retrieved_context="The baseline uses 800-character chunks with 100 characters of overlap.",
        generated_answer="The system uses 800-character chunks.",
        reference_answer="800-character chunks with 100 characters of overlap.",
        metadata={
            "required_facts": ["800-character chunks", "100 characters of overlap"],
            "relevant_documents": ["chunking"],
            "retrieved_documents": ["chunking"],
        },
    )
    assert res.metrics.correctness == 0.5
    assert res.details["satisfied_facts"] == ["800-character chunks"]
    assert res.details["missing_facts"] == ["100 characters of overlap"]
    assert res.failure_classification == "generation_failure"


@pytest.mark.asyncio
async def test_correctness_empty_answer(evaluator: DeterministicGenerationEvaluator) -> None:
    res = await evaluator.evaluate(
        question="What chunk size is used?",
        retrieved_context="800-character chunks.",
        generated_answer="",
        reference_answer="800-character chunks.",
        metadata={
            "required_facts": ["800-character chunks"],
            "relevant_documents": ["chunking"],
            "retrieved_documents": ["chunking"],
        },
    )
    assert res.metrics.correctness == 0.0
    assert res.failure_classification == "generation_failure"


# --- Faithfulness Tests ---


@pytest.mark.asyncio
async def test_faithfulness_fully_supported(evaluator: DeterministicGenerationEvaluator) -> None:
    context = "RAGBench uses Qdrant for vector storage and performs cosine-distance search."
    answer = "Qdrant is used for vector storage with cosine-distance search."
    res = await evaluator.evaluate(
        question="Which vector store is used?",
        retrieved_context=context,
        generated_answer=answer,
        reference_answer="Qdrant with cosine distance.",
        metadata={"relevant_documents": ["retrieval"], "retrieved_documents": ["retrieval"]},
    )
    assert res.metrics.faithfulness == 1.0
    assert len(res.details["unsupported_claims"]) == 0


@pytest.mark.asyncio
async def test_faithfulness_unsupported_claim(evaluator: DeterministicGenerationEvaluator) -> None:
    context = "The baseline uses fixed-size character chunks with 800 characters."
    answer = "RAGBench uses Pinecone database with hybrid BM25 and sparse vector indices."
    res = await evaluator.evaluate(
        question="How does retrieval work?",
        retrieved_context=context,
        generated_answer=answer,
        reference_answer="Qdrant dense retrieval.",
        metadata={"relevant_documents": ["retrieval"], "retrieved_documents": ["retrieval"]},
    )
    assert res.metrics.faithfulness < 0.7
    assert len(res.details["unsupported_claims"]) > 0
    assert res.failure_classification == "grounding_failure"


@pytest.mark.asyncio
async def test_faithfulness_mixed_claims(evaluator: DeterministicGenerationEvaluator) -> None:
    context = "RAGBench V1 accepts UTF-8 plain-text and Markdown files."
    answer = "RAGBench V1 accepts UTF-8 plain-text files. It also connects directly to Oracle SQL."
    res = await evaluator.evaluate(
        question="What files are accepted?",
        retrieved_context=context,
        generated_answer=answer,
        reference_answer="UTF-8 plain-text and Markdown.",
        metadata={"relevant_documents": ["ingestion"], "retrieved_documents": ["ingestion"]},
    )
    assert 0.0 < res.metrics.faithfulness < 1.0


@pytest.mark.asyncio
async def test_faithfulness_empty_context_unsupported(
    evaluator: DeterministicGenerationEvaluator,
) -> None:
    res = await evaluator.evaluate(
        question="What is the answer?",
        retrieved_context="",
        generated_answer="The answer is definitely 42 and Paris is the capital.",
        reference_answer="Unknown",
        metadata={"relevant_documents": ["doc1"], "retrieved_documents": []},
    )
    assert res.metrics.faithfulness == 0.0
    assert res.failure_classification == "retrieval_failure"


@pytest.mark.asyncio
async def test_faithfulness_empty_context_recognized_insufficient(
    evaluator: DeterministicGenerationEvaluator,
) -> None:
    res = await evaluator.evaluate(
        question="What is the answer?",
        retrieved_context="",
        generated_answer="The available context is insufficient to answer this question.",
        reference_answer="Unknown",
        metadata={"relevant_documents": ["doc1"], "retrieved_documents": []},
    )
    # Stating insufficient context when context is empty is faithful!
    assert res.metrics.faithfulness == 1.0


# --- Context Relevance Tests ---


@pytest.mark.asyncio
async def test_context_relevance_fully_relevant(
    evaluator: DeterministicGenerationEvaluator,
) -> None:
    res = await evaluator.evaluate(
        question="Where is doc1?",
        retrieved_context="Content of doc1",
        generated_answer="Answer from doc1",
        reference_answer="doc1",
        metadata={
            "relevant_documents": ["doc1"],
            "retrieved_documents": ["doc1", "doc1"],
        },
    )
    # Rank 1 hit (0.5) + 100% relevant ratio (0.5) = 1.0
    assert res.metrics.context_relevance == 1.0


@pytest.mark.asyncio
async def test_context_relevance_partial_relevant(
    evaluator: DeterministicGenerationEvaluator,
) -> None:
    res = await evaluator.evaluate(
        question="Where is doc1?",
        retrieved_context="Content",
        generated_answer="Answer",
        reference_answer="doc1",
        metadata={
            "relevant_documents": ["doc1"],
            "retrieved_documents": ["doc1", "doc2", "doc3", "doc4"],
        },
    )
    # Rank 1 hit (0.5) + 1/4 ratio (0.125) = 0.625
    assert res.metrics.context_relevance == 0.625


@pytest.mark.asyncio
async def test_context_relevance_irrelevant(evaluator: DeterministicGenerationEvaluator) -> None:
    res = await evaluator.evaluate(
        question="Where is doc1?",
        retrieved_context="Content",
        generated_answer="Answer",
        reference_answer="doc1",
        metadata={
            "relevant_documents": ["doc1"],
            "retrieved_documents": ["doc2", "doc3"],
        },
    )
    # Rank 1 hit (0) + 0 ratio = 0.0
    assert res.metrics.context_relevance == 0.0
    assert res.failure_classification == "retrieval_failure"
