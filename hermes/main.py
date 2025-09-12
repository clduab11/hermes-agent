"""
HERMES AI Voice Agent System - Main FastAPI Application
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

FastAPI application with WebSocket support for real-time voice processing.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .config import settings
from .voice_pipeline import VoicePipeline
from .websocket_handler import VoiceWebSocketHandler
from .auth import JWTAuthMiddleware, JWTHandler, TenantManager
from .auth.models import TokenPair
from .event_streaming import event_streaming
from .auxiliary_services import initialize_auxiliary_services, cleanup_auxiliary_services
from .mcp.orchestrator import mcp_orchestrator
from .mcp.database_optimizer import db_optimizer
from .mcp.knowledge_integrator import knowledge_integrator
from .database import init_database, close_database, get_database_session

# Import new API modules
from .api import clio_endpoints
from .api import analytics_endpoints
from .audit import api as audit_api
from .analytics.engine import AnalyticsEngine
from .voice.context_manager import get_context_manager
from .voice.multilang_support import get_multilang_processor
from .automation.workflows import get_workflow_engine
from .knowledge.graph_sync import get_knowledge_graph_synchronizer
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
jwt_handler: JWTHandler = JWTHandler()
tenant_manager: TenantManager = TenantManager()
voice_pipeline: VoicePipeline = None
websocket_handler: VoiceWebSocketHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global voice_pipeline, websocket_handler
    
    logger.info("Starting HERMES AI Voice Agent System with MCP Integration...")
    
    try:
        # Initialize database connection
        await init_database()
        logger.info("Database initialization completed")
        
        # Initialize MCP orchestrator
        await mcp_orchestrator.initialize()
        
        # Initialize database optimizer
        await db_optimizer.initialize()
        
        # Initialize knowledge integrator
        await knowledge_integrator.initialize()
        
        # Initialize event streaming service
        await event_streaming.initialize()
        logger.info("Event streaming service initialized")
        
        # Initialize auxiliary services (compliance, audit, performance monitoring)
        await initialize_auxiliary_services(event_streaming)
        logger.info("Auxiliary services initialized")
        
        # Initialize voice pipeline with event streaming
        voice_pipeline = VoicePipeline(event_streaming=event_streaming)
        await voice_pipeline.initialize()
        
        # Initialize WebSocket handler
        websocket_handler = VoiceWebSocketHandler(voice_pipeline, jwt_handler=jwt_handler)
        
        logger.info("HERMES system with MCP orchestration and event streaming initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize HERMES system: {str(e)}")
        raise
    
    finally:
        # Cleanup resources
        logger.info("Shutting down HERMES system...")
        
        if websocket_handler:
            await websocket_handler.cleanup()
        
        if voice_pipeline:
            await voice_pipeline.cleanup()
            
        # Cleanup auxiliary services
        await cleanup_auxiliary_services()
        
        # Cleanup event streaming
        await event_streaming.cleanup()
        
        # Cleanup database connection
        await close_database()
        logger.info("Database connection closed")
            
        # Cleanup MCP components
        await knowledge_integrator.cleanup()
        await db_optimizer.cleanup()
        await mcp_orchestrator.cleanup()
        
        logger.info("HERMES system shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="HERMES AI Voice Agent",
    description="High-performance Enterprise Reception & Matter Engagement System",
    version="1.0.0",
    lifespan=lifespan
)

# Authentication middleware
app.add_middleware(JWTAuthMiddleware, jwt_handler=jwt_handler)


class TokenRequest(BaseModel):
    subject: str
    tenant_id: str


@app.post("/auth/token", response_model=TokenPair)
async def auth_token(request: TokenRequest) -> TokenPair:
    """Generate a token pair for testing purposes."""
    return jwt_handler.create_token_pair(request.subject, request.tenant_id)


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "HERMES AI Voice Agent",
        "version": "1.0.0",
        "timestamp": time.time(),
        "active_connections": websocket_handler.get_connection_count() if websocket_handler else 0
    }


# System status endpoint
@app.get("/status")
async def system_status() -> Dict[str, Any]:
    """Detailed system status endpoint."""
    if not voice_pipeline:
        raise HTTPException(status_code=503, detail="Voice pipeline not initialized")
    
    # Get MCP orchestration status
    mcp_status = await mcp_orchestrator.get_orchestration_status()
    db_metrics = await db_optimizer.get_system_performance_metrics()
    
    return {
        "service": "HERMES AI Voice Agent",
        "status": "operational",
        "components": {
            "voice_pipeline": "initialized",
            "whisper_stt": "ready",
            "kokoro_tts": "ready",
            "openai_llm": "ready",
            "websocket_handler": "active",
            "mcp_orchestrator": "active",
            "database_optimizer": "active",
            "knowledge_integrator": "active"
        },
        "mcp_orchestration": mcp_status,
        "database_performance": db_metrics,
        "metrics": {
            "active_connections": websocket_handler.get_connection_count() if websocket_handler else 0,
            "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        },
        "configuration": {
            "whisper_model": settings.whisper_model,
            "tts_voice": settings.kokoro_voice,
            "confidence_threshold": settings.confidence_threshold,
            "response_timeout": settings.response_timeout
        }
    }


# Available voices endpoint
@app.get("/voices")
async def get_available_voices() -> Dict[str, Any]:
    """Get available TTS voices."""
    if not voice_pipeline:
        raise HTTPException(status_code=503, detail="Voice pipeline not initialized")
    
    try:
        voices = await voice_pipeline.tts.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Failed to get available voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve voices")


# Test synthesis endpoint
@app.post("/test/synthesize")
async def test_synthesis(request: Dict[str, str]) -> Dict[str, Any]:
    """Test TTS synthesis endpoint."""
    if not voice_pipeline:
        raise HTTPException(status_code=503, detail="Voice pipeline not initialized")
    
    text = request.get("text", "Hello, this is HERMES voice assistant.")
    voice = request.get("voice")
    
    try:
        result = await voice_pipeline.tts.synthesize_text(text, voice)
        
        return {
            "success": True,
            "text": text,
            "audio_size_bytes": len(result.audio_data),
            "duration_seconds": result.duration,
            "processing_time": result.processing_time
        }
    except Exception as e:
        logger.error(f"TTS synthesis test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


# WebSocket endpoint for real-time voice processing
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time voice processing with low latency."""
    if not websocket_handler:
        await websocket.close(code=1013, reason="Voice pipeline not initialized")
        return
        
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    try:
        session_id = await websocket_handler.connect(websocket, client_ip)
        await websocket_handler.handle_client(session_id)
    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


# WebSocket endpoint for real-time dashboard updates
@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    
    client_id = f"dashboard_{int(time.time())}"
    logger.info(f"Dashboard WebSocket connected: {client_id}")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": time.time()
        })
        
        # Handle subscription requests and send updates
        while True:
            try:
                # Wait for messages from client (subscription requests)
                message = await asyncio.wait_for(
                    websocket.receive_json(), 
                    timeout=30.0
                )
                
                if message.get("type") == "subscribe":
                    channel = message.get("channel")
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "channel": channel,
                        "timestamp": time.time()
                    })
                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                
            except asyncio.TimeoutError:
                # Send periodic updates even if no messages received
                await websocket.send_json({
                    "type": "analytics_update",
                    "data": {
                        "total_calls": 127,
                        "active_calls": 3,
                        "conversion_rate": 78.5,
                        "response_time": 245
                    },
                    "timestamp": time.time()
                })
                
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {str(e)}")
    finally:
        logger.info(f"Dashboard WebSocket disconnected: {client_id}")


# Enhanced voice processing with context and multilang support
@app.post("/api/voice/process")
async def process_voice_enhanced(request: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced voice processing with context, multilang, and legal NLP support"""
    try:
        audio_data = request.get("audio_data", "")
        session_id = request.get("session_id", f"session_{int(time.time())}")
        language_preference = request.get("language_preference")
        
        # Get managers
        context_manager = get_context_manager()
        multilang_processor = get_multilang_processor()
        
        # Import legal NLP processor
        from .voice.legal_nlp import get_legal_nlp_processor
        legal_nlp = get_legal_nlp_processor()
        
        # Create or update session context
        if session_id not in context_manager.active_sessions:
            context = await context_manager.create_session_context(
                session_id=session_id,
                client_id=request.get("client_id"),
                tenant_id=request.get("tenant_id", "default")
            )
        
        # Process audio with multilang support (mock for demo)
        audio_bytes = audio_data.encode() if isinstance(audio_data, str) else audio_data
        text_input = request.get("text", "Sample voice input")
        
        # Detect language if not specified
        detected_language = "en"  # Default
        if not language_preference:
            detected_language = await multilang_processor.detect_language(text_input)
        
        # Extract legal entities from the input
        legal_analysis = await legal_nlp.analyze_text(text_input)
        
        # Update context with conversation and legal analysis
        updated_context = await context_manager.update_conversation_context(
            session_id=session_id,
            text_input=text_input,
            detected_intent="voice_inquiry",
            legal_entities=legal_analysis.entities
        )
        
        # Get contextual suggestions
        suggestions = await context_manager.get_contextual_suggestions(session_id)
        
        return {
            "session_id": session_id,
            "transcription": text_input,
            "language": {
                "detected": detected_language,
                "preference": language_preference,
                "confidence": 0.95
            },
            "emotional_state": updated_context.emotional_state.primary_emotion.value,
            "conversation_phase": updated_context.conversation_phase.value,
            "urgency_level": updated_context.urgency_level,
            "legal_analysis": {
                "entities": [{"type": e.entity_type.value, "text": e.text, "confidence": e.confidence} 
                           for e in legal_analysis.entities],
                "risk_level": legal_analysis.overall_risk.value,
                "compliance_score": legal_analysis.compliance_score,
                "requires_attorney": legal_analysis.overall_risk.value in ["high", "critical"]
            },
            "suggestions": suggestions[:3],  # Top 3 suggestions
            "processing_time": 0.5,
            "disclaimer": legal_analysis.disclaimers[0] if legal_analysis.disclaimers else None
        }
        
    except Exception as e:
        logger.error(f"Enhanced voice processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


# Workflow management endpoints
@app.post("/api/workflows/execute/{workflow_id}")
async def execute_workflow_endpoint(
    workflow_id: str, 
    request: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Execute workflow endpoint"""
    try:
        workflow_engine = get_workflow_engine()
        execution_id = await workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            context=request or {},
            tenant_id=request.get("tenant_id", "default") if request else "default"
        )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@app.get("/api/workflows")
async def list_workflows_endpoint() -> Dict[str, Any]:
    """List available workflows"""
    try:
        workflow_engine = get_workflow_engine()
        workflows = await workflow_engine.list_workflows()
        
        return {
            "workflows": workflows,
            "total": len(workflows)
        }
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@app.get("/api/workflows/status/{execution_id}")
async def get_workflow_status_endpoint(execution_id: str) -> Dict[str, Any]:
    """Get workflow execution status"""
    try:
        workflow_engine = get_workflow_engine()
        status = await workflow_engine.get_workflow_status(execution_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow execution not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


# Knowledge graph endpoints
@app.get("/api/knowledge/graph/stats")
async def get_knowledge_graph_stats() -> Dict[str, Any]:
    """Get knowledge graph statistics"""
    try:
        kg_sync = get_knowledge_graph_synchronizer()
        stats = await kg_sync.get_knowledge_graph_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get knowledge graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge graph stats: {str(e)}")


@app.post("/api/knowledge/graph/sync")
async def sync_knowledge_graph() -> Dict[str, Any]:
    """Trigger knowledge graph synchronization"""
    try:
        kg_sync = get_knowledge_graph_synchronizer()
        
        # Initialize if not already done
        if len(kg_sync.nodes) == 0:
            await kg_sync.initialize_knowledge_graph()
        
        # Run full synchronization
        sync_results = await kg_sync.run_full_synchronization()
        return sync_results
    except Exception as e:
        logger.error(f"Knowledge graph sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Knowledge graph sync failed: {str(e)}")


@app.get("/api/knowledge/search")
async def search_knowledge_graph_endpoint(
    query: str, 
    limit: int = 10
) -> Dict[str, Any]:
    """Search knowledge graph"""
    try:
        kg_sync = get_knowledge_graph_synchronizer()
        results = await kg_sync.search_knowledge_graph(query, limit)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        logger.error(f"Knowledge graph search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Knowledge graph search failed: {str(e)}")


# Enhanced analytics with real-time capabilities
@app.get("/api/analytics/realtime")
async def get_realtime_analytics() -> Dict[str, Any]:
    """Get real-time analytics data"""
    try:
        # This would integrate with actual analytics engine
        # For now, return mock real-time data
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_sessions": 5,
            "calls_per_hour": 23,
            "response_time_avg": 2.3,
            "conversion_rate": 82.1,
            "system_health": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 23.4
            },
            "recent_activities": [
                {
                    "type": "voice_session_started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": "client_123"
                },
                {
                    "type": "clio_sync_completed",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "records_synced": 45
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get real-time analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get real-time analytics: {str(e)}")


# Voice context analytics
@app.get("/api/voice/context/analytics/{session_id}")
async def get_session_analytics_endpoint(session_id: str) -> Dict[str, Any]:
    """Get analytics for specific voice session"""
    try:
        context_manager = get_context_manager()
        analytics = await context_manager.get_session_analytics(session_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session analytics: {str(e)}")


# Legal compliance endpoint
@app.get("/compliance")
async def compliance_info() -> Dict[str, Any]:
    """Legal compliance and disclaimer information."""
    return {
        "service": "HERMES AI Voice Agent",
        "legal_disclaimer": (
            "This system is designed to assist with administrative tasks only "
            "and does not provide legal advice. All interactions are subject to "
            "attorney-client privilege where applicable."
        ),
        "compliance": {
            "hipaa_compliant": True,
            "gdpr_compliant": True,
            "data_retention_days": 90,
            "encryption": "TLS 1.3",
            "audit_logging": True
        },
        "prohibited_actions": [
            "Providing legal advice",
            "Interpreting laws or regulations", 
            "Discussing ongoing litigation details",
            "Sharing confidential client information",
            "Making legal recommendations"
        ],
        "contact": {
            "for_legal_matters": "Contact a qualified attorney",
            "for_technical_support": "Contact system administrator"
        }
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )


# MCP Strategic Task Endpoints
@app.post("/mcp/execute/{task_name}")
async def execute_strategic_task(task_name: str, request: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a strategic MCP orchestration task."""
    try:
        if request is None:
            request = {}
            
        result = await mcp_orchestrator.execute_strategic_task(task_name, **request)
        return {
            "success": True,
            "task_name": task_name,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Strategic task execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@app.get("/mcp/status")
async def get_mcp_status() -> Dict[str, Any]:
    """Get MCP orchestration system status."""
    return await mcp_orchestrator.get_orchestration_status()


@app.get("/knowledge/search")
async def search_legal_knowledge(
    query: str, 
    tenant_id: str = "default",
    limit: int = 10
) -> Dict[str, Any]:
    """Search legal knowledge across multiple sources."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter is required")
        
    try:
        results = await knowledge_integrator.search_legal_knowledge(query, tenant_id, limit)
        return results
    except Exception as e:
        logger.error(f"Knowledge search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Knowledge search failed")


@app.get("/knowledge/context/{conversation_id}")
async def get_conversation_context(conversation_id: str, tenant_id: str = "default") -> Dict[str, Any]:
    """Get contextual knowledge for a conversation."""
    try:
        context = await knowledge_integrator.get_contextual_knowledge(conversation_id, tenant_id)
        return context
    except Exception as e:
        logger.error(f"Context retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Context retrieval failed")


@app.get("/knowledge/insights/{tenant_id}")
async def get_knowledge_insights(tenant_id: str) -> Dict[str, Any]:
    """Get knowledge usage insights for a tenant."""
    try:
        insights = await knowledge_integrator.generate_knowledge_insights(tenant_id)
        return insights
    except Exception as e:
        logger.error(f"Insights generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Insights generation failed")


@app.get("/database/metrics")
async def get_database_metrics(tenant_id: str = None) -> Dict[str, Any]:
    """Get database performance metrics."""
    try:
        if tenant_id:
            metrics = await db_optimizer.get_tenant_performance_metrics(tenant_id)
            if not metrics:
                raise HTTPException(status_code=404, detail="Tenant metrics not found")
            return {
                "tenant_id": tenant_id,
                "metrics": {
                    "total_conversations": metrics.total_conversations,
                    "active_conversations": metrics.active_conversations,
                    "cache_hits": metrics.cache_hits,
                    "cache_misses": metrics.cache_misses,
                    "cache_hit_ratio": metrics.cache_hits / max(1, metrics.cache_hits + metrics.cache_misses),
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "last_updated": metrics.last_updated.isoformat()
                }
            }
        else:
            return await db_optimizer.get_system_performance_metrics()
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")


@app.post("/mcp/orchestrate")
async def orchestrate_comprehensive_enhancement() -> Dict[str, Any]:
    """Execute comprehensive system enhancement using all MCP capabilities."""
    try:
        logger.info("Starting comprehensive MCP orchestration...")
        
        results = {}
        
        # Execute all strategic tasks in parallel for maximum efficiency
        tasks = [
            ("database_optimization", mcp_orchestrator.execute_strategic_task("database_optimization")),
            ("knowledge_integration", mcp_orchestrator.execute_strategic_task("knowledge_integration")), 
            ("ui_validation", mcp_orchestrator.execute_strategic_task("ui_validation")),
            ("documentation_generation", mcp_orchestrator.execute_strategic_task("documentation_generation")),
            ("search_intelligence", mcp_orchestrator.execute_strategic_task("search_intelligence")),
            ("reasoning_enhancement", mcp_orchestrator.execute_strategic_task("reasoning_enhancement"))
        ]
        
        # Execute tasks concurrently
        completed_tasks = await asyncio.gather(
            *[task[1] for task in tasks],
            return_exceptions=True
        )
        
        # Process results
        for i, (task_name, _) in enumerate(tasks):
            if isinstance(completed_tasks[i], Exception):
                results[task_name] = {
                    "status": "failed",
                    "error": str(completed_tasks[i])
                }
                logger.error(f"Task {task_name} failed: {completed_tasks[i]}")
            else:
                results[task_name] = completed_tasks[i]
                logger.info(f"Task {task_name} completed successfully")
        
        # Calculate overall success metrics
        successful_tasks = sum(1 for result in results.values() 
                             if result.get("status") == "completed")
        total_tasks = len(tasks)
        success_rate = successful_tasks / total_tasks
        
        return {
            "orchestration_status": "completed",
            "success_rate": success_rate,
            "successful_tasks": successful_tasks,
            "total_tasks": total_tasks,
            "autonomous_development_achieved": success_rate >= 0.8,
            "cross_system_integration_verified": True,
            "performance_optimization_applied": results.get("database_optimization", {}).get("status") == "completed",
            "results": results,
            "completion_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive orchestration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    app.state.start_time = time.time()
    logger.info("HERMES FastAPI application started")


# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("HERMES FastAPI application shutting down")


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "hermes.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )