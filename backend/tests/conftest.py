"""Fixture pytest.

Database test:
- Pakai `TEST_DATABASE_URL` bila diset.
- Selain itu turunkan dari DATABASE_URL dengan sufiks `_test` (untuk PostgreSQL),
  atau SQLite lokal bila DATABASE_URL sudah sqlite.

Untuk menjalankan tanpa PostgreSQL (verifikasi lokal):
    TEST_DATABASE_URL=sqlite:///./_test_rme.db pytest
"""

from __future__ import annotations

import os
from collections.abc import Generator

import app.models  # noqa: F401  # register model ke metadata
import pytest
from app.api.deps import get_db
from app.core.config import get_settings
from app.db.base import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _build_test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = get_settings().database_url
    if base.startswith("sqlite"):
        return "sqlite:///./_test_rme.db"
    url = make_url(base)
    return str(url.set(database=f"{url.database or 'rme_stt'}_test"))


@pytest.fixture(scope="session")
def engine():
    url = _build_test_database_url()
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    else:
        engine = create_engine(url, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    from app.main import app

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
