from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from ragbench.app.schemas.rag import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe: returns 200 if the process is running. Fast, no external calls."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
)
async def ready(request: Request) -> JSONResponse | ReadyResponse:
    """Readiness probe: returns 200 if required local application services are initialized."""
    services = getattr(request.app.state, "services", None)
    if services is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": {"services": "uninitialized"}},
        )
    return ReadyResponse(
        status="ready",
        checks={
            "services": "initialized",
            "pipeline": "ready",
            "vector_store": "ready",
        },
    )
