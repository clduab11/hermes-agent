#!/usr/bin/env python3
"""
HERMES Core Voice Pipeline Demo with Event Streaming
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

Demonstrates the real-time voice pipeline with Redis pub/sub event streaming
and auxiliary services (compliance, audit, performance monitoring).
"""
import asyncio
import logging
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_event_streaming():
    """Demonstrate event streaming functionality."""
    print("🎙️  HERMES Core Voice Pipeline - Event Streaming Demo")
    print("=" * 60)
    
    try:
        # Import HERMES components
        from hermes.event_streaming import event_streaming, VoiceEvent, EventType
        from hermes.auxiliary_services import initialize_auxiliary_services
        from hermes.voice_pipeline import VoicePipeline
        
        print("✓ HERMES modules imported successfully")
        
        # Initialize event streaming (without Redis for demo)
        print("\n📡 Initializing Event Streaming Service...")
        streaming_success = await event_streaming.initialize()
        
        if streaming_success:
            print("✓ Event streaming initialized with Redis")
        else:
            print("⚠️  Event streaming initialized without Redis (demo mode)")
        
        # Initialize auxiliary services
        print("\n🔧 Initializing Auxiliary Services...")
        await initialize_auxiliary_services(event_streaming)
        print("✓ Compliance, Audit, and Performance monitoring services initialized")
        
        # Initialize voice pipeline with event streaming
        print("\n🎯 Initializing Voice Pipeline...")
        voice_pipeline = VoicePipeline(event_streaming=event_streaming)
        await voice_pipeline.initialize()
        print("✓ Voice pipeline initialized successfully")
        
        # Demonstrate event publishing
        print("\n📢 Publishing Sample Events...")
        
        session_id = str(uuid4())
        tenant_id = "demo_tenant"
        correlation_id = str(uuid4())
        
        # Simulate voice interaction events
        events = [
            VoiceEvent(
                event_type=EventType.VOICE_INTERACTION_STARTED,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id="demo_user",
                timestamp=datetime.now(timezone.utc),
                data={"audio_size_bytes": 1024},
                metadata={"demo": True},
                correlation_id=correlation_id
            ),
            VoiceEvent(
                event_type=EventType.STT_PROCESSED,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id="demo_user",
                timestamp=datetime.now(timezone.utc),
                data={
                    "transcription": {"text": "Hello, I need help with my case", "confidence": 0.95},
                    "processing_time_ms": 45
                },
                metadata={"stt_model": "whisper"},
                correlation_id=correlation_id
            ),
            VoiceEvent(
                event_type=EventType.COMPLIANCE_CHECK_REQUIRED,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id="demo_user",
                timestamp=datetime.now(timezone.utc),
                data={
                    "violation_type": "potential_legal_advice_request",
                    "description": "User mentioned 'case' - may require human review",
                    "severity": "medium"
                },
                metadata={"source": "compliance_validation"},
                correlation_id=correlation_id
            ),
            VoiceEvent(
                event_type=EventType.PERFORMANCE_METRICS_UPDATED,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id="demo_user",
                timestamp=datetime.now(timezone.utc),
                data={
                    "alert_type": "performance_target_met",
                    "total_processing_time_ms": 85,
                    "target_ms": 100,
                    "performance_status": "excellent"
                },
                metadata={"source": "performance_monitoring"},
                correlation_id=correlation_id
            )
        ]
        
        for i, event in enumerate(events, 1):
            success = await event_streaming.publish_event(event)
            status = "✓ Published" if success else "⚠️  Queued (Redis unavailable)"
            print(f"  {i}. {event.event_type.value}: {status}")
            await asyncio.sleep(0.1)  # Small delay for demo
        
        # Show stream info
        print("\n📊 Event Streaming Status:")
        stream_info = await event_streaming.get_stream_info(tenant_id="demo_tenant")
        for key, value in stream_info.items():
            print(f"  • {key}: {value}")
        
        # Demonstrate voice pipeline capabilities
        print("\n🎤 Voice Pipeline Capabilities:")
        print("  • STT → LLM → TTS processing with <100ms target")
        print("  • Real-time event streaming to auxiliary services")
        print("  • Compliance validation and prohibited content detection")
        print("  • Comprehensive audit logging with PII protection")
        print("  • Performance monitoring and optimization alerts")
        print("  • Multi-tenant data isolation and security")
        
        print("\n🏗️  Architecture: Hybrid Real-Time Orchestrator")
        print("  • WebSocket hot path for critical voice processing")
        print("  • Redis pub/sub for asynchronous auxiliary services")
        print("  • Tenant-isolated event streams for compliance")
        print("  • Automatic performance optimization recommendations")
        
        print("\n📈 Performance Targets:")
        print("  • <100ms end-to-end voice response time")
        print("  • Support for 1,000+ concurrent legal consultations")
        print("  • HIPAA/GDPR compliant data handling")
        print("  • Immutable audit trails for all interactions")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await voice_pipeline.cleanup()
        await event_streaming.cleanup()
        print("✓ Cleanup completed")
        
        print("\n🎉 HERMES Core Voice Pipeline Demo Completed Successfully!")
        print("\nNext Steps:")
        print("  1. Configure Redis server for production event streaming")
        print("  2. Set up Supabase for multi-tenant data persistence")
        print("  3. Configure OpenAI API for LLM processing")
        print("  4. Deploy with proper TLS certificates")
        print("  5. Run load testing for 1,000+ concurrent users")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        logger.exception("Demo failed")
        sys.exit(1)


async def main():
    """Main demo function."""
    await demo_event_streaming()


if __name__ == "__main__":
    asyncio.run(main())