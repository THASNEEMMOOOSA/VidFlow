# backend/app/db/session.py
"""
Database session management module.
Handles database connections and session creation.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create database engine with connection pooling
# The engine is responsible for managing connections to the database
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,        # Number of connections to maintain in pool
    max_overflow=20,     # Maximum overflow connections
    echo=settings.ENVIRONMENT == "development"  # Log SQL in development
)

# Create session factory
# SessionLocal will create new database sessions when called
SessionLocal = sessionmaker(
    autocommit=False,    # Don't auto-commit transactions
    autoflush=False,     # Don't auto-flush changes
    bind=engine          # Use the engine we created
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.
    This function is used by FastAPI dependencies to provide
    database sessions to route handlers.
    
    Yields:
        Session: A database session
        
    Note:
        The session is automatically closed after the request completes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()