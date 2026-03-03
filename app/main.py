"""Point d'entrée FastAPI - French Voice Learning API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarrage / arrêt de l'application."""
    await init_db()
    yield
    # Nettoyage si besoin (ex: fermer pool DB)


def create_app() -> FastAPI:
    """Factory de l'application FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
