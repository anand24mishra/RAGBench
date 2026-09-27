from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from ragbench.app.schemas.rag import IngestResponse, QueryRequest, RAGResponse

router = APIRouter(tags=["rag"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest(request: Request, file: Annotated[UploadFile, File()]) -> IngestResponse:
    max_bytes = request.app.state.settings.max_upload_bytes
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Document exceeds the {max_bytes}-byte upload limit",
        )
    return await request.app.state.services.ingestion.ingest(file.filename or "document", content)


@router.post("/query", response_model=RAGResponse)
async def query(payload: QueryRequest, request: Request) -> RAGResponse:
    return await request.app.state.services.pipeline.query(
        payload.query,
        payload.top_k,
        request_id=request.state.request_id,
    )
