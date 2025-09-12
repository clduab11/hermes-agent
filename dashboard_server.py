"""
Ultra-minimal HERMES dashboard server for testing
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import uvicorn

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
    return {
        "id": "demo_user",
        "name": "Demo Attorney",
        "email": "demo@hermes-ai.com",
        "role": "Senior Attorney",
        "avatar_url": "/static/assets/default-avatar.png",
        "tenant_id": "demo_tenant",
        "permissions": ["dashboard:read", "analytics:read", "clio:read", "audit:read"]
    }

@app.get("/api/analytics/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data."""
    return {
        "status": "success",
        "data": {
            "total_calls": 127,
            "calls_trend": "+12%",
            "conversion_rate": 78.5,
            "conversion_trend": "+5%", 
            "response_time": 245,
            "response_trend": "-15ms",
            "satisfaction": 4.7,
            "satisfaction_trend": "+0.2"
        },
        "time_range": "day",
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/api/analytics/dashboard/charts/call-volume")
async def get_call_volume_chart():
    """Get call volume chart data."""
    return {
        "status": "success", 
        "data": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "datasets": [{
                "label": "Calls",
                "data": [45, 52, 38, 67, 73, 29, 34],
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "borderColor": "rgb(59, 130, 246)",
                "borderWidth": 2,
                "fill": True
            }]
        },
        "time_range": "week"
    }

@app.get("/api/analytics/dashboard/charts/revenue")
async def get_revenue_chart():
    """Get revenue impact chart data."""
    return {
        "status": "success",
        "data": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [
                {
                    "label": "Potential Revenue",
                    "data": [12500, 15200, 18900, 16700],
                    "backgroundColor": "rgba(251, 191, 36, 0.1)",
                    "borderColor": "rgb(251, 191, 36)",
                    "borderWidth": 2
                },
                {
                    "label": "Converted Revenue", 
                    "data": [8750, 11400, 14200, 12300],
                    "backgroundColor": "rgba(34, 197, 94, 0.1)",
                    "borderColor": "rgb(34, 197, 94)",
                    "borderWidth": 2
                }
            ]
        },
        "time_range": "month"
    }

@app.get("/api/analytics/dashboard/recent-activity")
async def get_recent_activity():
    """Get recent activity feed for dashboard."""
    activities = [
        {
            "id": "activity_1",
            "type": "voice_call",
            "description": "Voice interaction completed with high satisfaction",
            "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            "user": "System",
            "details": {
                "duration": "2m 45s",
                "satisfaction": 4.8,
                "converted": True
            }
        },
        {
            "id": "activity_2", 
            "type": "client_update",
            "description": "New client record created: Johnson Law Firm",
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "user": "demo@hermes-ai.com",
            "details": {
                "client_id": "client_123",
                "practice_area": "Corporate Law"
            }
        },
        {
            "id": "activity_3",
            "type": "system_alert",
            "description": "Voice response time improved by 15ms", 
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "user": "System",
            "details": {
                "old_time": "260ms",
                "new_time": "245ms",
                "improvement": "15ms"
            }
        },
        {
            "id": "activity_4",
            "type": "integration",
            "description": "Clio sync completed successfully",
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            "user": "Integration",
            "details": {
                "synced_records": 45,
                "status": "success"
            }
        }
    ]
    
    return {
        "status": "success",
        "data": activities,
        "total_count": len(activities)
    }

@app.get("/api/analytics/voice/status")
async def get_voice_system_status():
    """Get voice system status for dashboard indicator."""
    return {
        "status": "success",
        "data": {
            "status": "ready",
            "indicator_color": "green",
            "status_text": "Voice Ready",
            "last_interaction": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "health_score": 0.95,
            "active_sessions": 2
        }
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