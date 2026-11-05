from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

# pool_pre_ping: Azure SQL drops idle connections (and serverless auto-pause
# drops all of them), so a pooled connection can be dead by the time a request
# picks it up - without the ping that request 500s instead of reconnecting.
engine = create_engine(settings.database_url, connect_args=_connect_args,
                       pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
