"""Simple in-memory tenant management."""

from __future__ import annotations

import uuid
from typing import Dict, Optional

from .models import Tenant


class TenantManager:
    """Manages tenant registration and lookup."""

    def __init__(self) -> None:
        self._tenants: Dict[str, Tenant] = {}

    def create_tenant(self, name: str, tier: str) -> Tenant:
        tenant = Tenant(id=str(uuid.uuid4()), name=name, tier=tier)
        self._tenants[tenant.id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)
