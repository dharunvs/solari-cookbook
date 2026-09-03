"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

from noxyn_api import __version__
from noxyn_api.database import database_is_ready
from noxyn_api.onboarding import router as onboarding_router
from noxyn_api.proposals import router as proposals_router
from noxyn_api.runs import router as runs_router

DatabaseProbe = Callable[[], Awaitable[bool]]


class HealthResponse(BaseModel):
    """Readiness information safe to expose without authentication."""

    status: Literal["ok"] = "ok"
    service: Literal["noxyn-api"] = "noxyn-api"
    version: str
    database: Literal["connected"] = "connected"


def create_app(*, database_probe: DatabaseProbe = database_is_ready) -> FastAPI:
    """Create an API instance with an injectable readiness probe."""
    application = FastAPI(
        title="Noxyn-Solari API",
        version=__version__,
        description="Noxyn finds API ecosystem drift; Solari proves it.",
    )
    application.state.database_probe = database_probe
    application.include_router(onboarding_router)
    application.include_router(runs_router)
    application.include_router(proposals_router)

    @application.get(
        "/health",
        operation_id="getHealth",
        response_model=HealthResponse,
        tags=["system"],
    )
    async def get_health(request: Request) -> HealthResponse:
        """Report readiness only after PostgreSQL responds."""
        probe: DatabaseProbe = request.app.state.database_probe
        if not await probe():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            )
        return HealthResponse(version=__version__)

    return application


app = create_app()
