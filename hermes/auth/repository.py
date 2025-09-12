"""Authentication repository for user management."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Role, User, UserCreate, UserUpdate
from ..database.security import DatabaseSecurityManager
from ..security.validation import validate_email, sanitize_text

logger = logging.getLogger(__name__)


class AuthRepository:
    """Repository for authentication and user management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate, tenant_id: str) -> User:
        """Create a new user with proper validation and security."""
        # Validate email
        if not validate_email(user_data.email):
            raise ValueError("Invalid email format")
        
        # Sanitize inputs
        email = sanitize_text(user_data.email.lower())
        full_name = sanitize_text(user_data.full_name)
        
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        try:
            # Set tenant context for RLS
            await DatabaseSecurityManager.set_tenant_context(self.session, tenant_id)
            
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # Insert new user
            stmt = insert(User).values(
                id=user_id,
                email=email,
                full_name=full_name,
                password_hash=user_data.password_hash,
                tenant_id=tenant_id,
                roles=user_data.roles or [Role.STAFF],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            # Retrieve and return the created user
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID with tenant isolation."""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with tenant isolation."""
        try:
            stmt = select(User).where(User.email == email.lower())
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            update_values = {}
            
            if user_data.full_name is not None:
                update_values["full_name"] = sanitize_text(user_data.full_name)
            
            if user_data.email is not None:
                if not validate_email(user_data.email):
                    raise ValueError("Invalid email format")
                update_values["email"] = sanitize_text(user_data.email.lower())
            
            if user_data.password_hash is not None:
                update_values["password_hash"] = user_data.password_hash
            
            if user_data.roles is not None:
                update_values["roles"] = user_data.roles
            
            if user_data.is_active is not None:
                update_values["is_active"] = user_data.is_active
            
            update_values["updated_at"] = datetime.now(timezone.utc)
            
            stmt = update(User).where(User.id == user_id).values(**update_values)
            await self.session.execute(stmt)
            await self.session.commit()
            
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise

    async def delete_user(self, user_id: str) -> bool:
        """Soft delete a user (set inactive)."""
        try:
            stmt = update(User).where(User.id == user_id).values(
                is_active=False,
                updated_at=datetime.now(timezone.utc)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete user: {e}")
            return False

    async def get_users_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users for a tenant with pagination."""
        try:
            await DatabaseSecurityManager.set_tenant_context(self.session, tenant_id)
            
            stmt = (
                select(User)
                .where(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get users by tenant: {e}")
            return []

    async def update_user_roles(self, user_id: str, roles: list[Role]) -> Optional[User]:
        """Update user roles."""
        try:
            stmt = update(User).where(User.id == user_id).values(
                roles=roles,
                updated_at=datetime.now(timezone.utc)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update user roles: {e}")
            raise

    async def get_users_by_role(self, tenant_id: str, role: Role) -> list[User]:
        """Get all users with a specific role in a tenant."""
        try:
            await DatabaseSecurityManager.set_tenant_context(self.session, tenant_id)
            
            # Using PostgreSQL array contains operator
            stmt = select(User).where(
                User.is_active == True,
                User.roles.contains([role])
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get users by role: {e}")
            return []

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        try:
            stmt = update(User).where(User.id == user_id).values(
                last_login_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update last login: {e}")

    async def search_users(
        self, 
        tenant_id: str, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[User]:
        """Search users by email or name within a tenant."""
        try:
            await DatabaseSecurityManager.set_tenant_context(self.session, tenant_id)
            
            search_term = f"%{sanitize_text(query).lower()}%"
            
            stmt = (
                select(User)
                .where(
                    User.is_active == True,
                    (User.email.ilike(search_term) | User.full_name.ilike(search_term))
                )
                .offset(skip)
                .limit(limit)
                .order_by(User.full_name)
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            return []