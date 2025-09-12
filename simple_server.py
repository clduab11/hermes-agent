"""
Simplified HERMES server for testing dashboard functionality
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import new API modules
from hermes.api import clio_endpoints
from hermes.api import analytics_endpoints
from hermes.audit import api as audit_api

# Create FastAPI app
app = FastAPI(
    title="HERMES AI Voice Agent - Dashboard Demo",
    description="High-performance Enterprise Reception & Matter Engagement System",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(clio_endpoints.router)
app.include_router(analytics_endpoints.router) 
app.include_router(audit_api.router)

# Demo page endpoint
@app.get("/")
async def demo_page():
    """Serve the demo page."""
    return FileResponse("static/demo.html")

# Dashboard endpoint  
@app.get("/dashboard")
async def dashboard():
    """Serve the professional dashboard."""
    return FileResponse("static/dashboard/index.html")

@app.get("/api/auth/user")
async def get_current_user_info():
    """Get current user information for dashboard."""
    # Mock user data for demo
    return {
        "id": "demo_user",
        "name": "Demo Attorney",
        "email": "demo@hermes-ai.com",
        "role": "Senior Attorney",
        "avatar_url": "/static/assets/default-avatar.png",
        "tenant_id": "demo_tenant",
        "permissions": ["dashboard:read", "analytics:read", "clio:read", "audit:read"]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "HERMES AI Voice Agent Dashboard",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)