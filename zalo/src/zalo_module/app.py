"""FastAPI application factory — decision sheet section 7.

``create_app(settings)`` wires ``app.state.settings`` / ``app.state.engine`` —
the attribute names both ``api.*._deps`` helpers read first — then mounts the
``/intake/v1`` routers. Startup configures the audit log and runs migrations
so a fresh runtime dir is self-initializing.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from zalo_module import audit
from zalo_module.api import connector as connector_api
from zalo_module.api import intake as intake_api
from zalo_module.api import ocr_requests as ocr_requests_api
from zalo_module.database import get_engine, init_db
from zalo_module.settings import Settings


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Re-configure is harmless (same path) and keeps the app self-sufficient
    # when create_app is used without cli.py having configured audit first.
    audit.configure(app.state.settings.access_log_path)
    init_db(app.state.engine)
    yield


def create_app(settings: Settings) -> FastAPI:
    # configure before get_engine so the db file access itself is logged.
    audit.configure(settings.access_log_path)
    engine = get_engine(settings)
    app = FastAPI(title="zalo-intake", lifespan=_lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.include_router(intake_api.router)
    app.include_router(ocr_requests_api.router)
    app.include_router(connector_api.router)
    # No connector auto-spawn here — POST /connector/v1/connectors/start is
    # the only trigger (deliberate; see docs/migration-notes.md).
    return app
