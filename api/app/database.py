"""Configuración de SQLAlchemy: engine, sesión y dependencia get_db."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# pool_pre_ping evita usar conexiones muertas tras reinicios de SQL Server.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI que entrega una sesión y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
