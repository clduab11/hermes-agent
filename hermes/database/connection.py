"""
Database connection management for HERMES system.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from ..config import settings

logger = logging.getLogger(__name__)

# Database base model
Base = declarative_base()

# Global database engine and session maker
_engine = None
_session_factory = None


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Supabase database connection only."""
        global _engine, _session_factory

        # Enforce Supabase-only connection for SaaS deployment
        supabase_url = settings.secure_database_url

        if not supabase_url:
            logger.error("SUPABASE DATABASE REQUIRED: This SaaS version requires Supabase database connection. Local databases are not supported.")
            raise RuntimeError("Supabase database URL required for enterprise SaaS deployment")

        # Validate that it's a Supabase URL for security
        if not ("supabase.co" in supabase_url or "supabase.in" in supabase_url):
            logger.error("SECURITY VIOLATION: Only Supabase database connections are allowed in enterprise SaaS mode")
            raise RuntimeError("Invalid database provider: Enterprise SaaS requires Supabase")

        try:
            # Ensure proper async driver for Supabase
            db_url = supabase_url
            if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

            # Create async engine with enterprise security settings
            self.engine = create_async_engine(
                db_url,
                echo=False,  # Never echo in production SaaS
                pool_pre_ping=True,
                pool_recycle=1800,  # Shorter recycle for security
                pool_size=20,  # Enterprise connection pool
                max_overflow=10,
                connect_args={
                    "server_settings": {
                        "application_name": "hermes_enterprise_saas",
                        "statement_timeout": "30000",  # 30 second timeout
                    }
                }
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Set global references
            _engine = self.engine
            _session_factory = self.session_factory

            self._initialized = True
            logger.info("Enterprise Supabase database connection initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Supabase database connection: {e}")
            logger.error("Enterprise SaaS deployment requires valid Supabase connection")
            raise RuntimeError(f"Supabase connection failed: {e}")

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._initialized or not self.session_factory:
            raise RuntimeError("Database not initialized")

        return self.session_factory()

    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_session() -> Optional[AsyncSession]:
    """Get a database session if available."""
    try:
        if db_manager._initialized:
            return await db_manager.get_session()
        return None
    except Exception as e:
        logger.error(f"Failed to get database session: {e}")
        return None


async def init_database() -> bool:
    """Initialize the database connection."""
    return await db_manager.initialize()


async def close_database():
    """Close the database connection."""
    await db_manager.close()
