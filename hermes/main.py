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

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .config import settings
from .voice_pipeline import VoicePipeline
from .websocket_handler import VoiceWebSocketHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
voice_pipeline: VoicePipeline = None
websocket_handler: VoiceWebSocketHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global voice_pipeline, websocket_handler
    
    logger.info("Starting HERMES AI Voice Agent System...")
    
    try:
        # Initialize voice pipeline
        voice_pipeline = VoicePipeline()
        await voice_pipeline.initialize()
        
        # Initialize WebSocket handler
        websocket_handler = VoiceWebSocketHandler(voice_pipeline)
        
        logger.info("HERMES system initialized successfully")
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
        
        logger.info("HERMES system shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="HERMES AI Voice Agent",
    description="High-performance Enterprise Reception & Matter Engagement System",
    version="1.0.0",
    lifespan=lifespan
)

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


# Demo page endpoint
@app.get("/")
async def demo_page():
    """Serve the demo page."""
    return FileResponse("static/demo.html")


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
    
    return {
        "service": "HERMES AI Voice Agent",
        "status": "operational",
        "components": {
            "voice_pipeline": "initialized",
            "whisper_stt": "ready",
            "kokoro_tts": "ready",
            "openai_llm": "ready",
            "websocket_handler": "active"
        },
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


# WebSocket endpoint for voice interactions
@app.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time voice interactions."""
    if not websocket_handler:
        await websocket.close(code=1011, reason="Service not available")
        return
    
    # Get client information
    client_ip = websocket.client.host
    
    try:
        # Accept connection
        session_id = await websocket_handler.connect(websocket, client_ip)
        
        # Handle client messages
        await websocket_handler.handle_client_messages(session_id)
        
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


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