from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure the platform root is on sys.path
platform_root = Path(__file__).resolve().parent.parent
if str(platform_root) not in sys.path:
    sys.path.insert(0, str(platform_root))

from api.config import get_settings
from api.database import init_db
from api.routers import backtests, stocks, strategies, universe


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Backtesting Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(stocks.router)
    app.include_router(strategies.router)
    app.include_router(backtests.router)
    app.include_router(universe.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # Serve frontend static files in production
    frontend_dist = platform_root / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


app = create_app()
