"""
Database connection management for HERMES system.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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
        """Initialize database connection."""
        global _engine, _session_factory
        
        if not settings.database_url:
            logger.warning("No database URL configured - operating in mock mode")
            return False
        
        try:
            db_url = settings.database_url
            # Normalize to asyncpg driver for async engine
            if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

            # Create async engine
            self.engine = create_async_engine(
                db_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Set global references
            _engine = self.engine
            _session_factory = self.session_factory
            
            self._initialized = True
            logger.info("Database connection initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
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
