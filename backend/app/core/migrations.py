"""
Apply Alembic migrations programmatically (API start-up, worker start-up, CLI, tests).

Databases created before Alembic existed (by ``Base.metadata.create_all``) have the
baseline tables but no ``alembic_version`` table. They are brought to the baseline
(missing Phase 0 tables created), stamped as ``0001_baseline``, then upgraded normally.
"""
import logging
import os
import threading

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.database import Base, engine

logger = logging.getLogger(__name__)

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASELINE_REVISION = "0001_baseline"
_BASELINE_TABLES = (
    "users", "projects", "assets", "jobs", "job_outputs", "usage_events", "access_keys", "job_leases",
)
_lock = threading.Lock()
_done = False


def alembic_config() -> Config:
    cfg = Config(os.path.join(_BACKEND_ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(_BACKEND_ROOT, "migrations"))
    return cfg


def upgrade_database(force: bool = False) -> None:
    global _done
    with _lock:
        if _done and not force:
            return
        from app.models import entities  # noqa: F401  (register tables)

        cfg = alembic_config()
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            tables = set(inspect(connection).get_table_names())
            if "alembic_version" not in tables and "jobs" in tables:
                logger.warning("Pre-Alembic database detected: creating missing baseline tables and stamping %s.",
                               BASELINE_REVISION)
                legacy = [Base.metadata.tables[t] for t in _BASELINE_TABLES if t not in tables]
                if legacy:
                    # Tables added in Phase 0 that are absent from very old databases.
                    Base.metadata.create_all(bind=connection, tables=legacy)
                command.stamp(cfg, BASELINE_REVISION)
            command.upgrade(cfg, "head")
        _done = True
