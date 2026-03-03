"""Configuration de la base de données asynchrone SQLAlchemy."""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()


def _database_url_without_schema(url: str) -> str:
    """Retire le paramètre 'schema' de l'URL (asyncpg ne le supporte pas)."""
    parsed = urlparse(url)
    if not parsed.query:
        return url
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop("schema", None)
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


database_url = _database_url_without_schema(settings.DATABASE_URL)

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base pour tous les modèles SQLAlchemy."""

    pass


# Import des modèles pour enregistrer les tables avec Base.metadata
from app import models  # noqa: F401, E402


async def get_db() -> AsyncSession:
    """Dépendance FastAPI : session DB asynchrone par requête."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Crée les tables (à appeler au démarrage)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
