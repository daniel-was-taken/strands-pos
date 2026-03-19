"""FastAPI application — REST API and web UI for the database assistant.

Run locally:  uvicorn server.api:app --reload
API docs:     http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.responses import StreamingResponse

load_dotenv()

from server.log_stream import install_log_handler, log_event_generator
from server.core.orchestrator import DatabaseOrchestrator
from server.db.repository import get_connection, run_migrations
from server.schemas import (
    ApprovalRequest,
    ApprovalResponse,
    ErrorResponse,
    HealthResponse,
    QueryRequest,
    QueryStatusResponse,
    QuerySubmitResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_log_handler()
    logger.info("Running database migrations")
    run_migrations()
    logger.info("Migrations complete, starting server")
    yield


app = FastAPI(
    title="Strands POS API",
    lifespan=lifespan,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)


orchestrator = DatabaseOrchestrator()


@app.get("/logs/stream")
async def stream_logs() -> StreamingResponse:
    return StreamingResponse(
        log_event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
def home() -> FileResponse:
    return FileResponse("server/static/index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/ready", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Readiness check — verifies the database is reachable."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return HealthResponse()


@app.post("/query", response_model=QuerySubmitResponse, status_code=201)
def submit_query(payload: QueryRequest) -> QuerySubmitResponse:
    result = orchestrator.submit_query(payload.query)
    return QuerySubmitResponse(**result)


@app.get("/query/{request_id}", response_model=QueryStatusResponse)
def get_query_status(request_id: str) -> QueryStatusResponse:
    result = orchestrator.get_request(request_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return QueryStatusResponse(**result)


@app.post("/approval/{approval_id}", response_model=ApprovalResponse)
def decide_approval(
    approval_id: str,
    payload: ApprovalRequest,
) -> ApprovalResponse:
    result = orchestrator.decide_approval(
        approval_id=approval_id,
        decision=payload.decision,
        reviewer=payload.reviewer,
        reason=payload.reason,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApprovalResponse(**result)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            detail="An unexpected error occurred.",
        ).model_dump(),
    )
