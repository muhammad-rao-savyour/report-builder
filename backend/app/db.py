"""Database connection.

Scalability notes baked in here:
  pool_pre_ping  - checks a connection is alive before using it, so an RDS
                   failover does not throw errors at your users.
  pool_size      - each API server keeps a SMALL pool. 10 servers x 5 = 50
                   connections. RDS db.t4g.micro allows about 60, so keep this
                   number low and multiply in your head before scaling out.
  pool_recycle   - drops connections after 30 min, avoids stale-connection bugs.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency. One session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
