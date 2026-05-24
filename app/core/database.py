from sqlmodel import SQLModel, create_engine, Session
from app.core.config import get_settings
import os

# Import all models so SQLModel.metadata is populated
from app.models.user import User
from app.models.document import Document
from app.models.requirement import Requirement
from app.models.analysis import AnalysisRun
from app.models.finding import Finding

settings = get_settings()

def get_engine():
    """Create database engine with appropriate settings for SQLite or PostgreSQL."""
    database_url = settings.DATABASE_URL

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            echo=False
        )
    else:
        # PostgreSQL + PGVector configuration
        engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )

    return engine


engine = get_engine()


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """Create all tables. For PostgreSQL, ensure pgvector extension exists."""
    # Create pgvector extension if using PostgreSQL
    if str(engine.url).startswith("postgresql"):
        with engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()

    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully.")
