from logging.config import fileConfig

import app.models  # noqa: F401  # register semua model ke metadata
from alembic import context

# Pastikan package aplikasi ter-import sehingga Base.metadata terisi.
from app.core.config import get_settings  # noqa: F401
from app.db.base import Base
from sqlalchemy import create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Jalankan migrasi dalam mode offline (tanpa koneksi DB, menghasilkan SQL)."""
    context.configure(
        url=_get_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Jalankan migrasi dengan koneksi DB langsung."""
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
