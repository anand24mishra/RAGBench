from __future__ import annotations

from dataclasses import dataclass

from ragbench.app.context.builder import ContextBuilder
from ragbench.app.core.config import Settings
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder
from ragbench.app.generation.base import LLMProvider
from ragbench.app.generation.factory import create_llm_provider
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.pipeline.rag import RAGPipeline
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.base import VectorStore
from ragbench.app.vector_store.qdrant import QdrantVectorStore


@dataclass
class AppServices:
    ingestion: IngestionService
    pipeline: RAGPipeline
    vector_store: VectorStore
    llm_provider: LLMProvider

    async def close(self) -> None:
        await self.llm_provider.close()
        await self.vector_store.close()


async def build_services(settings: Settings) -> AppServices:
    embedder = SentenceTransformerEmbedder(
        settings.embedding_model,
        batch_size=settings.embedding_batch_size,
    )
    vector_store = QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection)
    await vector_store.ensure_collection(embedder.dimension)
    llm_provider = create_llm_provider(settings)
    ingestion = IngestionService(
        loader=DocumentLoader(),
        chunker=FixedSizeChunker(settings.chunk_size, settings.chunk_overlap),
        embedder=embedder,
        vector_store=vector_store,
    )
    pipeline = RAGPipeline(
        retriever=SemanticRetriever(embedder, vector_store, settings.top_k),
        context_builder=ContextBuilder(settings.context_char_limit),
        llm_provider=llm_provider,
    )
    return AppServices(
        ingestion=ingestion,
        pipeline=pipeline,
        vector_store=vector_store,
        llm_provider=llm_provider,
    )
