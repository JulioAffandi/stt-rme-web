from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine = None
_session_factory: sessionmaker[Session] | None = None


def get_engine():
    """Singleton engine SQLAlchemy (dibuat sekali per proses)."""
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def SessionLocal() -> Session:
    """Helper pembuat session mandiri untuk background tasks atau worker."""
    return get_session_factory()()


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI: satu session per request."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
