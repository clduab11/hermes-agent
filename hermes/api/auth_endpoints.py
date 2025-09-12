"""Authentication API endpoints."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.jwt_handler import JWTHandler
from ..auth.models import Role, TokenPair, User, UserCreate, UserUpdate
from ..auth.rbac import require_roles
from ..auth.repository import AuthRepository
from ..database.security import SecureAsyncSession
from ..security.validation import validate_email, sanitize_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


async def get_db_session() -> AsyncSession:
    """Dependency to get database session."""
    # This would typically use dependency injection from your database setup
    # For now, this is a placeholder that should be replaced with actual session
    pass


async def get_auth_repository(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    """Dependency to get auth repository."""
    return AuthRepository(session)


async def get_current_user(
    request: Request,
    auth_repo: AuthRepository = Depends(get_auth_repository)
) -> User:
    """Get the current authenticated user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await auth_repo.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> User:
    """Register a new user (admin only)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    try:
        user = await auth_repo.create_user(user_data, tenant_id)
        logger.info(f"User registered: {user.email} in tenant {tenant_id}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenPair)
async def login(
    email: str,
    password: str,
    jwt_handler: JWTHandler = Depends(),
    auth_repo: AuthRepository = Depends(get_auth_repository)
) -> TokenPair:
    """Authenticate user and return JWT tokens."""
    try:
        # Validate and sanitize email
        email = sanitize_text(email.lower())
        if not validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Get user
        user = await auth_repo.get_user_by_email(email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password (implement your password hashing logic)
        # This is a placeholder - implement proper password verification
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        await auth_repo.update_last_login(user.id)
        
        # Create token pair
        tokens = jwt_handler.create_token_pair(
            subject=user.id,
            tenant_id=user.tenant_id,
            roles=user.roles
        )
        
        logger.info(f"User logged in: {user.email}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    refresh_token: str,
    jwt_handler: JWTHandler = Depends()
) -> TokenPair:
    """Refresh access token using refresh token."""
    try:
        tokens = jwt_handler.refresh(refresh_token)
        return tokens
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user information."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_repo: AuthRepository = Depends(get_auth_repository)
) -> User:
    """Update current user information."""
    try:
        # Users can't change their own roles through this endpoint
        user_data.roles = None
        
        updated_user = await auth_repo.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@router.get("/users", response_model=List[User])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> List[User]:
    """List all users in the tenant (admin only)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    users = await auth_repo.get_users_by_tenant(tenant_id, skip, limit)
    return users


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> User:
    """Get a specific user (admin only)."""
    user = await auth_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> User:
    """Update a user (admin only)."""
    try:
        updated_user = await auth_repo.update_user(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> dict:
    """Delete (deactivate) a user (admin only)."""
    success = await auth_repo.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}/roles", response_model=User)
async def update_user_roles(
    user_id: str,
    roles: List[Role],
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN))
) -> User:
    """Update user roles (admin only)."""
    try:
        updated_user = await auth_repo.update_user_roles(user_id, roles)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
    except Exception as e:
        logger.error(f"Role update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role update failed"
        )


@router.get("/users/search", response_model=List[User])
async def search_users(
    q: str,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    auth_repo: AuthRepository = Depends(get_auth_repository),
    _: None = Depends(require_roles(Role.ADMIN, Role.ATTORNEY))
) -> List[User]:
    """Search users by email or name."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    users = await auth_repo.search_users(tenant_id, q, skip, limit)
    return users


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    This is a placeholder - implement with proper password hashing library like bcrypt.
    """
    # TODO: Implement with proper password verification
    # Example: return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    return True  # Placeholder