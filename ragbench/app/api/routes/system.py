from __future__ import annotations

import sys
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/config")
async def get_system_config(request: Request) -> dict[str, Any]:
    """Return runtime configuration and environment info."""
    settings = getattr(request.app.state, "settings", None)
    chunk_size = getattr(settings, "chunk_size", 800) if settings else 800
    chunk_overlap = getattr(settings, "chunk_overlap", 100) if settings else 100
    top_k = getattr(settings, "top_k", 5) if settings else 5
    default_embed = "BAAI/bge-small-en-v1.5"
    embedding_provider = (
        getattr(settings, "embedding_provider", "fastembed") if settings else "fastembed"
    )
    embedding_model = (
        getattr(settings, "embedding_model", default_embed) if settings else default_embed
    )
    gen_model = getattr(settings, "llm_model", "mock-llm") if settings else "mock-llm"
    env = getattr(settings, "environment", "development") if settings else "development"

    return {
        "status": "online",
        "version": "0.1.0",
        "python_version": sys.version.split()[0],
        "configuration": {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "generation_model": gen_model,
            "vector_store": "qdrant",
            "environment": env,
        },
    }
