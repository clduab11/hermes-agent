#!/usr/bin/env python3
"""
Quick validation test for HERMES system improvements
"""
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_configuration():
    """Test configuration management."""
    try:
        from hermes.config import settings
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  - Debug mode: {settings.debug}")
        logger.info(f"  - API host: {settings.api_host}:{settings.api_port}")
        logger.info(f"  - Confidence threshold: {settings.confidence_threshold}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

async def test_analytics_engine():
    """Test analytics engine."""
    try:
        from hermes.analytics.engine import AnalyticsEngine, MetricType, AnalyticsMetric
        from datetime import datetime
        
        # Test without database (mock mode)
        engine = AnalyticsEngine(db_session=None)
        await engine.initialize()
        
        # Test metric recording
        metric = AnalyticsMetric(
            name="test_metric",
            value=123,
            timestamp=datetime.utcnow(),
            tenant_id="test_tenant",
            metric_type=MetricType.CALL_VOLUME
        )
        
        result = await engine.record_metric(metric)
        logger.info(f"✓ Analytics engine test passed (mock mode: {engine._mock_data_enabled})")
        return True
    except Exception as e:
        logger.error(f"✗ Analytics engine test failed: {e}")
        return False

async def test_legal_nlp():
    """Test legal NLP processor."""
    try:
        from hermes.voice.legal_nlp import get_legal_nlp_processor
        
        nlp = get_legal_nlp_processor()
        
        # Test text analysis
        test_text = "I need help with my contract dispute. The liability clause seems unclear."
        analysis = await nlp.analyze_text(test_text)
        
        logger.info(f"✓ Legal NLP test passed")
        logger.info(f"  - Entities found: {len(analysis.entities)}")
        logger.info(f"  - Risk level: {analysis.overall_risk.value}")
        logger.info(f"  - Compliance score: {analysis.compliance_score}")
        return True
    except Exception as e:
        logger.error(f"✗ Legal NLP test failed: {e}")
        return False

async def test_voice_context():
    """Test voice context manager."""
    try:
        from hermes.voice.context_manager import get_context_manager
        
        context_manager = get_context_manager()
        
        # Create test session
        session_id = "test_session"
        context = await context_manager.create_session_context(
            session_id=session_id,
            client_id="test_client",
            tenant_id="test_tenant"
        )
        
        # Update context
        updated_context = await context_manager.update_conversation_context(
            session_id=session_id,
            text_input="Hello, I need legal advice about my contract",
            detected_intent="legal_inquiry"
        )
        
        logger.info(f"✓ Voice context test passed")
        logger.info(f"  - Session created: {session_id}")
        logger.info(f"  - Emotional state: {updated_context.emotional_state.primary_emotion.value}")
        logger.info(f"  - Conversation phase: {updated_context.conversation_phase.value}")
        return True
    except Exception as e:
        logger.error(f"✗ Voice context test failed: {e}")
        return False

async def test_mcp_orchestrator():
    """Test MCP orchestrator."""
    try:
        from hermes.mcp.orchestrator import mcp_orchestrator
        
        # Initialize orchestrator
        await mcp_orchestrator.initialize()
        
        # Get status
        status = await mcp_orchestrator.get_orchestration_status()
        
        logger.info(f"✓ MCP orchestrator test passed")
        logger.info(f"  - Servers configured: {len(status['configured_servers'])}")
        logger.info(f"  - Healthy servers: {len(status['healthy_servers'])}")
        return True
    except Exception as e:
        logger.error(f"✗ MCP orchestrator test failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    logger.info("🧪 Running HERMES system validation tests...")
    
    tests = [
        ("Configuration Management", test_configuration),
        ("Analytics Engine", test_analytics_engine),
        ("Legal NLP Processor", test_legal_nlp),
        ("Voice Context Manager", test_voice_context),
        ("MCP Orchestrator", test_mcp_orchestrator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Testing {test_name}...")
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready.")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))