import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL.strip()

# Normalize connection string for SQLAlchemy with psycopg2 driver
# Render and cloud providers supply 'postgres://' or 'postgresql://'
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Check PostgreSQL reachability; fall back to local SQLite if unreachable
if "postgresql" in db_url:
    try:
        temp_engine = create_engine(db_url, connect_args={"connect_timeout": 3}, echo=False)
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        temp_engine.dispose()
    except Exception as e:
        sqlite_fallback = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'multimediatoolkit.db')}"
        logger.warning(
            f"Configured PostgreSQL database unreachable ({e}). "
            f"Activating zero-config local SQLite fallback at {sqlite_fallback}"
        )
        db_url = sqlite_fallback

# Configure SQLite or PostgreSQL engine appropriately
connect_args = {"check_same_thread": False, "timeout": 30} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
