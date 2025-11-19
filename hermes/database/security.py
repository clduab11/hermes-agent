"""Database security utilities for multi-tenant RLS and protection."""

from __future__ import annotations

import logging
from typing import Optional

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.tenant_context import tenant_context

logger = logging.getLogger(__name__)


class DatabaseSecurityManager:
    """Manages database security policies and RLS (Row Level Security)."""

    @staticmethod
    async def enable_rls_for_table(session: AsyncSession, table_name: str) -> None:
        """Enable Row Level Security for a table."""
        try:
            await session.execute(
                text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
            )
            await session.commit()
            logger.info(f"RLS enabled for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to enable RLS for {table_name}: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def create_tenant_policy(
        session: AsyncSession, table_name: str, policy_name: Optional[str] = None
    ) -> None:
        """Create RLS policy for tenant isolation."""
        if not policy_name:
            policy_name = f"tenant_isolation_{table_name}"

        try:
            # Drop existing policy if it exists
            drop_sql = f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"
            await session.execute(text(drop_sql))

            # Create new tenant isolation policy
            policy_sql = f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
            """
            await session.execute(text(policy_sql))
            await session.commit()
            logger.info(f"Tenant policy created for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create tenant policy for {table_name}: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
        """Set the current tenant context for RLS policies."""
        try:
            # Validate tenant_id to prevent SQL injection
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', tenant_id):
                raise ValueError(f"Invalid tenant_id format: {tenant_id}")

            # Use set_config function with parameterized query for security
            await session.execute(
                text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
                {"tenant_id": tenant_id}
            )
            logger.debug(f"Set database tenant context: {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to set tenant context: {e}")
            raise

    @staticmethod
    async def create_user_policy(
        session: AsyncSession, table_name: str, policy_name: Optional[str] = None
    ) -> None:
        """Create RLS policy for user-level access control."""
        if not policy_name:
            policy_name = f"user_access_{table_name}"

        try:
            # Drop existing policy if it exists
            drop_sql = f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"
            await session.execute(text(drop_sql))

            # Create user access policy
            policy_sql = f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING (
                user_id = current_setting('app.current_user', true)::uuid OR
                current_setting('app.user_role', true) = 'admin'
            )
            WITH CHECK (
                user_id = current_setting('app.current_user', true)::uuid OR
                current_setting('app.user_role', true) = 'admin'
            )
            """
            await session.execute(text(policy_sql))
            await session.commit()
            logger.info(f"User policy created for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create user policy for {table_name}: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def create_role_based_policy(
        session: AsyncSession,
        table_name: str,
        allowed_roles: list[str],
        policy_name: Optional[str] = None,
    ) -> None:
        """Create RLS policy based on user roles."""
        if not policy_name:
            policy_name = f"role_access_{table_name}"

        roles_condition = " OR ".join(
            [
                f"current_setting('app.user_role', true) = '{role}'"
                for role in allowed_roles
            ]
        )

        try:
            # Drop existing policy if it exists
            drop_sql = f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"
            await session.execute(text(drop_sql))

            # Create role-based policy
            policy_sql = f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING ({roles_condition})
            WITH CHECK ({roles_condition})
            """
            await session.execute(text(policy_sql))
            await session.commit()
            logger.info(f"Role-based policy created for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create role policy for {table_name}: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def setup_audit_triggers(session: AsyncSession, table_name: str) -> None:
        """Set up audit triggers for a table to track changes."""
        try:
            # Validate table name to prevent SQL injection
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                raise ValueError(f"Invalid table name: {table_name}. Only alphanumeric characters and underscores allowed.")

            if len(table_name) > 63:  # PostgreSQL identifier limit
                raise ValueError(f"Table name too long: {table_name}. Maximum 63 characters allowed.")

            # Create audit table if it doesn't exist (using SQL identifier escaping)
            audit_table = f"{table_name}_audit"

            # Validate audit table name as well
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', audit_table):
                raise ValueError(f"Invalid audit table name: {audit_table}")

            # Use parameterized query with identifier substitution for security
            from sqlalchemy.sql import text
            from sqlalchemy import MetaData, inspect

            # Check if audit table already exists
            inspector = inspect(session.bind)
            existing_tables = await session.run_sync(lambda sync_session: inspector.get_table_names())

            if audit_table not in existing_tables:
                create_audit_sql = text(f"""
                CREATE TABLE {audit_table} (
                    audit_id SERIAL PRIMARY KEY,
                    table_name VARCHAR(50) NOT NULL,
                    operation VARCHAR(10) NOT NULL,
                    old_data JSONB,
                    new_data JSONB,
                    user_id UUID,
                    tenant_id UUID,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                await session.execute(create_audit_sql)

            # Create audit trigger function (validated identifiers)
            trigger_function = text(f"""
            CREATE OR REPLACE FUNCTION audit_{table_name}() RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO {audit_table} (
                    table_name, operation, old_data, new_data,
                    user_id, tenant_id, timestamp
                ) VALUES (
                    TG_TABLE_NAME, TG_OP,
                    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
                    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
                    current_setting('app.current_user', true)::uuid,
                    current_setting('app.current_tenant', true)::uuid,
                    CURRENT_TIMESTAMP
                );
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END;
            $$ LANGUAGE plpgsql;
            """)  # nosec B608 - Table names are validated with regex above
            await session.execute(trigger_function)

            # Create trigger (validated identifiers)
            trigger_sql = text(f"""
            CREATE TRIGGER audit_{table_name}_trigger
                AFTER INSERT OR UPDATE OR DELETE ON {table_name}
                FOR EACH ROW EXECUTE FUNCTION audit_{table_name}()
            """)
            await session.execute(trigger_sql)

            await session.commit()
            logger.info(f"Audit triggers created for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create audit triggers for {table_name}: {e}")
            await session.rollback()
            raise


async def setup_connection_security(connection: asyncpg.Connection) -> None:
    """Configure connection-level security settings."""
    try:
        # Set secure connection parameters
        await connection.execute("SET timezone = 'UTC'")
        await connection.execute("SET statement_timeout = '30s'")
        await connection.execute("SET idle_in_transaction_session_timeout = '60s'")
        await connection.execute("SET lock_timeout = '10s'")

        # Prevent potential attacks
        await connection.execute(
            "SET log_statement = 'none'"
        )  # Disable statement logging

        logger.debug("Connection security settings applied")
    except Exception as e:
        logger.error(f"Failed to apply connection security: {e}")
        raise


class SecureAsyncSession:
    """Async database session with automatic tenant context management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._tenant_set = False
        self._user_set = False

    async def __aenter__(self):
        # Automatically set tenant context from current request
        current_tenant = tenant_context.get(None)
        if current_tenant:
            # Support both TenantContext objects and legacy string tenant IDs
            tenant_id = getattr(current_tenant, "tenant_id", current_tenant)
            await DatabaseSecurityManager.set_tenant_context(
                self.session, str(tenant_id)
            )
            self._tenant_set = True
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up context settings
        try:
            if self._tenant_set:
                await self.session.execute(text("RESET app.current_tenant"))
            if self._user_set:
                await self.session.execute(text("RESET app.current_user"))
                await self.session.execute(text("RESET app.user_role"))
        except Exception as e:
            logger.error(f"Failed to reset database context: {e}")

        await self.session.close()

    async def set_user_context(self, user_id: str, role: str) -> None:
        """Set user context for the session."""
        try:
            # Validate inputs to prevent SQL injection
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
                raise ValueError(f"Invalid user_id format: {user_id}")
            if not re.match(r'^[a-zA-Z0-9_]+$', role):
                raise ValueError(f"Invalid role format: {role}")

            # Use set_config function with parameterized queries for security
            await self.session.execute(
                text("SELECT set_config('app.current_user', :user_id, true)"),
                {"user_id": user_id}
            )
            await self.session.execute(
                text("SELECT set_config('app.user_role', :role, true)"),
                {"role": role}
            )
            self._user_set = True
            logger.debug(f"Set database user context: {user_id} with role {role}")
        except Exception as e:
            logger.error(f"Failed to set user context: {e}")
            raise
