from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ragbench.app.api.routes import evaluation, experiments, health, rag, system
from ragbench.app.core.config import Settings, get_settings
from ragbench.app.core.logging import configure_logging
from ragbench.app.domain.errors import (
    DocumentError,
    EmbeddingError,
    LLMProviderError,
    LLMTimeoutError,
    RAGBenchError,
    VectorStoreError,
)
from ragbench.app.services import AppServices, build_services


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    logging.getLogger("ragbench.api").warning(
        "request_error",
        extra={
            "event": "failure",
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_type": code,
            "status_code": status_code,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


def create_app(
    *,
    settings: Settings | None = None,
    services: AppServices | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    logger = logging.getLogger("ragbench.api")

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.settings = resolved_settings
        if getattr(application.state, "services", None) is None:
            application.state.services = services or await build_services(resolved_settings)
        try:
            yield
        finally:
            if getattr(application.state, "services", None) is not None:
                await application.state.services.close()

    application = FastAPI(
        title="RAGBench",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    if services is not None:
        application.state.services = services

    @application.middleware("http")
    async def request_logging(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "event": "failure",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise
        duration_ms = (perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "event": "request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
            },
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "request_validation_error",
            "Request validation failed",
        )

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
        return _error_response(request, exc.status_code, "http_error", message)

    @application.exception_handler(DocumentError)
    async def document_error(request: Request, exc: DocumentError) -> JSONResponse:
        return _error_response(request, status.HTTP_400_BAD_REQUEST, exc.code, str(exc))

    @application.exception_handler(LLMTimeoutError)
    async def llm_timeout(request: Request, exc: LLMTimeoutError) -> JSONResponse:
        return _error_response(request, status.HTTP_504_GATEWAY_TIMEOUT, exc.code, str(exc))

    @application.exception_handler(RAGBenchError)
    async def dependency_error(request: Request, exc: RAGBenchError) -> JSONResponse:
        status_code = status.HTTP_502_BAD_GATEWAY
        if not isinstance(exc, (EmbeddingError, VectorStoreError, LLMProviderError)):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return _error_response(request, status_code, exc.code, str(exc))

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(rag.router)
    application.include_router(evaluation.router)
    application.include_router(experiments.router)
    application.include_router(system.router)
    return application


app = create_app()
