import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQLITE_FALLBACK_URL = f"sqlite:///{os.path.join(_BACKEND_ROOT, 'multimediatoolkit.db')}"


class DatabaseConfigurationError(RuntimeError):
    pass


def normalize_database_url(url: str) -> str:
    """Render and other providers supply 'postgres://' or 'postgresql://'; use the psycopg2 driver."""
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _postgres_reachable(url: str) -> Exception | None:
    try:
        temp_engine = create_engine(url, connect_args={"connect_timeout": 3}, echo=False)
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        temp_engine.dispose()
        return None
    except Exception as e:  # noqa: BLE001 - any connection failure counts
        return e


def resolve_database_url(raw_url: str, is_development: bool, allow_sqlite_fallback: bool = True) -> str:
    """
    Decide which database to use.

    - Development: PostgreSQL if reachable, otherwise (optionally) local SQLite.
    - Anything else: PostgreSQL is mandatory. An unreachable database or a SQLite URL
      is a fatal error -- never a silent switch to an ephemeral file.
    """
    url = normalize_database_url(raw_url)

    if url.startswith("sqlite"):
        if not is_development:
            raise DatabaseConfigurationError(
                "SQLite is not allowed outside ENVIRONMENT=development. "
                "Set DATABASE_URL to a persistent PostgreSQL database."
            )
        return url

    if "postgresql" in url:
        err = _postgres_reachable(url)
        if err is None:
            return url
        if is_development and allow_sqlite_fallback:
            logger.warning(
                "Development mode: PostgreSQL unreachable (%s). Using local SQLite fallback at %s",
                err, SQLITE_FALLBACK_URL,
            )
            return SQLITE_FALLBACK_URL
        raise DatabaseConfigurationError(
            f"PostgreSQL database is unreachable ({type(err).__name__}). "
            "Refusing to start: silent fallback to SQLite would lose data."
        )

    return url


db_url = resolve_database_url(settings.DATABASE_URL, settings.is_development, settings.ALLOW_SQLITE_FALLBACK)

if db_url.startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False, "timeout": 30}, echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
else:
    # pool_pre_ping: serverless Postgres (e.g. Neon free tier) closes idle connections.
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
