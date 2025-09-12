"""
Minimal mock authentication for testing
"""

class MockUser:
    def __init__(self):
        self.id = "demo_user"
        self.email = "demo@hermes-ai.com"
        
class MockTenantContext:
    def __init__(self):
        self.tenant_id = "demo_tenant"

def get_current_user():
    return MockUser()

def require_permission(permission: str):
    def decorator(func):
        return func
    return decorator

def get_tenant_context():
    return MockTenantContext()