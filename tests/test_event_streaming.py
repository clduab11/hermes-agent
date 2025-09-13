"""
Tests for HERMES event streaming and auxiliary services.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from hermes.auxiliary_services import (
    AuditLoggingSubscriber,
    ComplianceValidationSubscriber,
    PerformanceMonitoringSubscriber,
)
from hermes.event_streaming import EventStreamingService, EventType, VoiceEvent


class TestEventStreamingService:
    """Test event streaming core functionality."""

    @pytest.fixture
    async def event_service(self):
        """Create event streaming service for testing."""
        service = EventStreamingService()
        # Mock Redis client for testing
        service.redis_client = AsyncMock()
        service.redis_client.ping = AsyncMock(return_value=True)
        service.redis_client.xadd = AsyncMock(return_value="123-0")
        service.redis_client.xgroup_create = AsyncMock()
        service.redis_client.xreadgroup = AsyncMock(return_value=[])
        service._running = True
        return service

    @pytest.mark.asyncio
    async def test_event_publishing(self, event_service):
        """Test event publishing functionality."""
        event = VoiceEvent(
            event_type=EventType.VOICE_INTERACTION_STARTED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id="test_user",
            timestamp=datetime.now(timezone.utc),
            data={"test": "data"},
            metadata={"source": "test"},
            correlation_id="test_correlation",
        )

        result = await event_service.publish_event(event)
        assert result is True

        # Verify Redis calls
        assert (
            event_service.redis_client.xadd.call_count == 2
        )  # tenant and global streams

    @pytest.mark.asyncio
    async def test_event_serialization(self):
        """Test event serialization and deserialization."""
        original_event = VoiceEvent(
            event_type=EventType.STT_PROCESSED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={"transcription": "Hello world"},
            metadata={"model": "whisper"},
            correlation_id="test_correlation",
        )

        # Serialize to dict
        event_dict = original_event.to_dict()
        assert event_dict["event_type"] == "stt_processed"
        assert event_dict["data"]["transcription"] == "Hello world"

        # Deserialize back to event
        restored_event = VoiceEvent.from_dict(event_dict)
        assert restored_event.event_type == original_event.event_type
        assert restored_event.session_id == original_event.session_id
        assert restored_event.data == original_event.data


class TestComplianceValidationSubscriber:
    """Test compliance validation functionality."""

    @pytest.fixture
    async def compliance_subscriber(self):
        """Create compliance validation subscriber for testing."""
        event_service = MagicMock()
        event_service.subscribe_to_events = AsyncMock(return_value=True)
        event_service.publish_event = AsyncMock()

        subscriber = ComplianceValidationSubscriber(event_service)
        await subscriber.initialize()
        return subscriber

    @pytest.mark.asyncio
    async def test_prohibited_content_detection(self, compliance_subscriber):
        """Test detection of prohibited legal advice requests."""
        test_event = VoiceEvent(
            event_type=EventType.STT_PROCESSED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={
                "transcription": {
                    "text": "What should I do about my lawsuit?",
                    "confidence": 0.95,
                }
            },
            metadata={},
            correlation_id="test",
        )

        await compliance_subscriber._process_compliance_event(test_event)

        # Should flag this as prohibited content
        compliance_subscriber.event_streaming.publish_event.assert_called_once()
        call_args = compliance_subscriber.event_streaming.publish_event.call_args[0][0]
        assert call_args.event_type == EventType.COMPLIANCE_CHECK_REQUIRED
        assert "prohibited_legal_advice_request" in call_args.data["violation_type"]

    @pytest.mark.asyncio
    async def test_ai_response_validation(self, compliance_subscriber):
        """Test validation of AI responses for legal advice."""
        test_event = VoiceEvent(
            event_type=EventType.LLM_PROCESSED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={"response_text": "You should definitely sue them for damages."},
            metadata={},
            correlation_id="test",
        )

        await compliance_subscriber._process_compliance_event(test_event)

        # Should flag AI providing legal advice
        compliance_subscriber.event_streaming.publish_event.assert_called_once()
        call_args = compliance_subscriber.event_streaming.publish_event.call_args[0][0]
        assert call_args.event_type == EventType.COMPLIANCE_CHECK_REQUIRED
        assert "ai_provided_legal_advice" in call_args.data["violation_type"]


class TestAuditLoggingSubscriber:
    """Test audit logging functionality."""

    @pytest.fixture
    async def audit_subscriber(self):
        """Create audit logging subscriber for testing."""
        event_service = MagicMock()
        event_service.subscribe_to_events = AsyncMock(return_value=True)

        subscriber = AuditLoggingSubscriber(event_service)
        await subscriber.initialize()
        return subscriber

    @pytest.mark.asyncio
    async def test_audit_entry_creation(self, audit_subscriber):
        """Test audit log entry creation."""
        test_event = VoiceEvent(
            event_type=EventType.VOICE_INTERACTION_COMPLETED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id="test_user",
            timestamp=datetime.now(timezone.utc),
            data={"total_processing_time": 0.085, "confidence_score": 0.95},
            metadata={"pipeline_success": True},
            correlation_id="test",
        )

        await audit_subscriber._process_audit_event(test_event)

        # Should create audit log entry
        assert len(audit_subscriber.audit_logs) == 1
        entry = audit_subscriber.audit_logs[0]
        assert entry["session_id"] == "test_session"
        assert entry["tenant_id"] == "test_tenant"
        assert entry["event_type"] == "voice_interaction_completed"
        assert "audit_id" in entry

    @pytest.mark.asyncio
    async def test_pii_detection(self, audit_subscriber):
        """Test PII detection in audit logging."""
        test_event = VoiceEvent(
            event_type=EventType.STT_PROCESSED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={
                "transcription": {
                    "text": "My phone number is 555-1234 and my email is john@example.com"
                }
            },
            metadata={},
            correlation_id="test",
        )

        await audit_subscriber._process_audit_event(test_event)

        entry = audit_subscriber.audit_logs[0]
        assert entry["compliance_metadata"]["contains_pii"] is True


class TestPerformanceMonitoringSubscriber:
    """Test performance monitoring functionality."""

    @pytest.fixture
    async def performance_subscriber(self):
        """Create performance monitoring subscriber for testing."""
        event_service = MagicMock()
        event_service.subscribe_to_events = AsyncMock(return_value=True)
        event_service.publish_event = AsyncMock()

        subscriber = PerformanceMonitoringSubscriber(event_service)
        await subscriber.initialize()
        return subscriber

    @pytest.mark.asyncio
    async def test_performance_tracking(self, performance_subscriber):
        """Test performance metrics tracking."""
        # Start interaction
        start_event = VoiceEvent(
            event_type=EventType.VOICE_INTERACTION_STARTED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={},
            metadata={},
            correlation_id="test",
        )

        await performance_subscriber._process_performance_event(start_event)
        assert "test_session" in performance_subscriber.session_timings

        # Complete interaction
        complete_event = VoiceEvent(
            event_type=EventType.VOICE_INTERACTION_COMPLETED,
            session_id="test_session",
            tenant_id="test_tenant",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            data={"total_processing_time": 0.150},  # 150ms - exceeds 100ms target
            metadata={},
            correlation_id="test",
        )

        await performance_subscriber._process_performance_event(complete_event)

        # Should trigger performance alert
        performance_subscriber.event_streaming.publish_event.assert_called_once()
        call_args = performance_subscriber.event_streaming.publish_event.call_args[0][0]
        assert call_args.event_type == EventType.PERFORMANCE_METRICS_UPDATED
        assert call_args.data["alert_type"] == "latency_exceeded"

    @pytest.mark.asyncio
    async def test_metrics_aggregation(self, performance_subscriber):
        """Test performance metrics aggregation."""
        # Add some sample metrics
        performance_subscriber.performance_metrics["stt_processing_time"] = [
            50,
            75,
            60,
            45,
            80,
        ]
        performance_subscriber.performance_metrics["llm_processing_time"] = [
            120,
            90,
            110,
            95,
            100,
        ]

        # Generate metrics report
        await performance_subscriber._generate_metrics_report()

        # Verify metrics calculations
        stt_metrics = performance_subscriber.performance_metrics["stt_processing_time"]
        assert len(stt_metrics) == 5
        avg_stt = sum(stt_metrics) / len(stt_metrics)
        assert avg_stt == 62.0


class TestIntegration:
    """Integration tests for the complete event streaming system."""

    @pytest.mark.asyncio
    async def test_end_to_end_event_flow(self):
        """Test complete event flow from voice interaction to auxiliary services."""
        # This would be a more complex integration test
        # For now, we verify that all components can be initialized together
        event_service = EventStreamingService()
        event_service.redis_client = AsyncMock()
        event_service.redis_client.ping = AsyncMock(return_value=True)
        event_service._running = True

        # Initialize all subscribers
        compliance_sub = ComplianceValidationSubscriber(event_service)
        audit_sub = AuditLoggingSubscriber(event_service)
        performance_sub = PerformanceMonitoringSubscriber(event_service)

        # Mock successful initialization
        event_service.subscribe_to_events = AsyncMock(return_value=True)

        compliance_result = await compliance_sub.initialize()
        audit_result = await audit_sub.initialize()
        performance_result = await performance_sub.initialize()

        assert compliance_result is True
        assert audit_result is True
        assert performance_result is True

        # Verify all subscribers are registered
        assert event_service.subscribe_to_events.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
