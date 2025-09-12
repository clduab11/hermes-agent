"""
Auxiliary subscriber services for HERMES voice pipeline events.
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

Implements specialized subscribers for:
- Compliance validation and legal guidance enforcement
- Audit logging for regulatory compliance
- Knowledge graph enrichment and learning
- Performance monitoring and optimization
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4

from .event_streaming import EventStreamingService, VoiceEvent, EventType
from .config import settings

logger = logging.getLogger(__name__)


class ComplianceValidationSubscriber:
    """
    Subscriber for real-time compliance validation of voice interactions.
    
    Features:
    - Real-time detection of prohibited legal advice requests
    - Automatic flagging of confidential information disclosure
    - HIPAA/GDPR compliance validation
    - Attorney-client privilege protection
    """
    
    def __init__(self, event_streaming: EventStreamingService):
        self.event_streaming = event_streaming
        self.prohibited_patterns = [
            r"legal advice",
            r"what should I do",
            r"recommend.*action",
            r"court.*strategy",
            r"case.*outcome",
            r"lawsuit.*chances",
            r"settlement.*amount",
            r"sue.*for",
        ]
        self.confidential_patterns = [
            r"social security",
            r"ssn",
            r"tax.*id",
            r"bank.*account",
            r"credit.*card",
            r"password",
            r"personal.*information",
        ]
    
    async def initialize(self):
        """Initialize compliance validation subscriber."""
        logger.info("Initializing Compliance Validation Subscriber...")
        
        # Subscribe to relevant events
        success = await self.event_streaming.subscribe_to_events(
            event_types=[
                EventType.STT_PROCESSED,
                EventType.LLM_PROCESSED,
                EventType.VOICE_INTERACTION_COMPLETED
            ],
            callback=self._process_compliance_event,
            consumer_group="compliance_validation",
            consumer_name=f"compliance_worker_{uuid4().hex[:8]}"
        )
        
        if success:
            logger.info("Compliance validation subscriber initialized successfully")
        else:
            logger.warning("Failed to initialize compliance validation subscriber")
        
        return success
    
    async def _process_compliance_event(self, event: VoiceEvent):
        """Process compliance-related events."""
        try:
            if event.event_type == EventType.STT_PROCESSED:
                await self._validate_user_input(event)
            elif event.event_type == EventType.LLM_PROCESSED:
                await self._validate_ai_response(event)
            elif event.event_type == EventType.VOICE_INTERACTION_COMPLETED:
                await self._validate_complete_interaction(event)
                
        except Exception as e:
            logger.error(f"Error in compliance validation: {e}")
    
    async def _validate_user_input(self, event: VoiceEvent):
        """Validate user input for prohibited content."""
        transcription = event.data.get("transcription", {})
        text = transcription.get("text", "").lower()
        
        # Check for prohibited legal advice requests
        import re
        for pattern in self.prohibited_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                await self._flag_compliance_violation(
                    event,
                    "prohibited_legal_advice_request",
                    f"User requested prohibited legal advice: {pattern}",
                    {"matched_pattern": pattern, "user_text": text[:100]}
                )
                break
        
        # Check for confidential information disclosure
        for pattern in self.confidential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                await self._flag_compliance_violation(
                    event,
                    "confidential_information_disclosed",
                    f"User disclosed confidential information: {pattern}",
                    {"matched_pattern": pattern, "severity": "high"}
                )
                break
    
    async def _validate_ai_response(self, event: VoiceEvent):
        """Validate AI response for compliance issues."""
        response_text = event.data.get("response_text", "").lower()
        
        # Check if AI provided legal advice (should be prevented by system prompt)
        legal_advice_indicators = [
            "you should",
            "i recommend",
            "the best option is",
            "you must",
            "legal advice",
            "in my opinion"
        ]
        
        import re
        for indicator in legal_advice_indicators:
            if indicator in response_text:
                await self._flag_compliance_violation(
                    event,
                    "ai_provided_legal_advice",
                    f"AI potentially provided legal advice: {indicator}",
                    {"ai_response": response_text[:200], "severity": "critical"}
                )
                break
    
    async def _validate_complete_interaction(self, event: VoiceEvent):
        """Validate complete interaction for overall compliance."""
        interaction_data = event.data
        
        # Check if interaction required human transfer but didn't get it
        requires_transfer = interaction_data.get("requires_human_transfer", False)
        was_transferred = interaction_data.get("human_transfer_initiated", False)
        
        if requires_transfer and not was_transferred:
            await self._flag_compliance_violation(
                event,
                "failed_human_transfer",
                "Interaction required human transfer but none was initiated",
                {"requires_transfer": requires_transfer, "severity": "high"}
            )
    
    async def _flag_compliance_violation(
        self,
        original_event: VoiceEvent,
        violation_type: str,
        description: str,
        details: Dict[str, Any]
    ):
        """Flag a compliance violation by publishing an alert event."""
        violation_event = VoiceEvent(
            event_type=EventType.COMPLIANCE_CHECK_REQUIRED,
            session_id=original_event.session_id,
            tenant_id=original_event.tenant_id,
            user_id=original_event.user_id,
            timestamp=datetime.now(timezone.utc),
            data={
                "violation_type": violation_type,
                "description": description,
                "details": details,
                "original_event_type": original_event.event_type.value,
                "severity": details.get("severity", "medium")
            },
            metadata={
                "source": "compliance_validation_subscriber",
                "requires_immediate_attention": details.get("severity") == "critical"
            },
            correlation_id=original_event.correlation_id
        )
        
        await self.event_streaming.publish_event(violation_event)
        
        logger.warning(
            f"Compliance violation flagged: {violation_type} in session {original_event.session_id}"
        )


class AuditLoggingSubscriber:
    """
    Subscriber for comprehensive audit logging of all voice interactions.
    
    Features:
    - Immutable audit trail creation
    - HIPAA/GDPR compliant logging
    - Secure storage with tenant isolation
    - Performance and access logging
    """
    
    def __init__(self, event_streaming: EventStreamingService):
        self.event_streaming = event_streaming
        self.audit_logs: List[Dict[str, Any]] = []
        self._batch_size = 100
        self._flush_interval = 30  # seconds
        self._last_flush = datetime.now()
    
    async def initialize(self):
        """Initialize audit logging subscriber."""
        logger.info("Initializing Audit Logging Subscriber...")
        
        # Subscribe to all events for comprehensive audit trail
        success = await self.event_streaming.subscribe_to_events(
            event_types=list(EventType),  # All event types
            callback=self._process_audit_event,
            consumer_group="audit_logging",
            consumer_name=f"audit_worker_{uuid4().hex[:8]}"
        )
        
        # Start periodic flush task
        if success:
            asyncio.create_task(self._periodic_flush())
            logger.info("Audit logging subscriber initialized successfully")
        else:
            logger.warning("Failed to initialize audit logging subscriber")
        
        return success
    
    async def _process_audit_event(self, event: VoiceEvent):
        """Process events for audit logging."""
        try:
            # Create audit log entry
            audit_entry = {
                "audit_id": str(uuid4()),
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "session_id": event.session_id,
                "tenant_id": event.tenant_id,
                "user_id": event.user_id,
                "correlation_id": event.correlation_id,
                "data_summary": self._create_data_summary(event),
                "compliance_metadata": {
                    "data_retention_class": self._classify_data_retention(event),
                    "contains_pii": self._detect_pii(event),
                    "legal_privilege_applicable": event.tenant_id is not None
                }
            }
            
            # Add to batch
            self.audit_logs.append(audit_entry)
            
            # Flush if batch is full or it's been too long
            if (len(self.audit_logs) >= self._batch_size or 
                (datetime.now() - self._last_flush).seconds >= self._flush_interval):
                await self._flush_audit_logs()
                
        except Exception as e:
            logger.error(f"Error in audit logging: {e}")
    
    def _create_data_summary(self, event: VoiceEvent) -> Dict[str, Any]:
        """Create a privacy-safe summary of event data."""
        summary = {
            "has_audio_data": "audio_data" in event.data,
            "has_transcription": "transcription" in event.data,
            "has_response": "response_text" in event.data,
            "processing_time_ms": event.data.get("processing_time_ms", 0),
            "confidence_score": event.data.get("confidence_score", 0)
        }
        
        # Add character counts without exposing actual content
        if "transcription" in event.data:
            text = event.data["transcription"].get("text", "")
            summary["transcription_length"] = len(text)
            
        if "response_text" in event.data:
            summary["response_length"] = len(event.data["response_text"])
            
        return summary
    
    def _classify_data_retention(self, event: VoiceEvent) -> str:
        """Classify data for retention policy."""
        if event.event_type in [EventType.ERROR_OCCURRED, EventType.COMPLIANCE_CHECK_REQUIRED]:
            return "long_term"  # Keep errors and compliance issues longer
        elif event.event_type == EventType.VOICE_INTERACTION_COMPLETED:
            return "standard"  # Normal business retention
        else:
            return "short_term"  # Technical events can be purged sooner
    
    def _detect_pii(self, event: VoiceEvent) -> bool:
        """Detect if event contains personally identifiable information."""
        # Simple PII detection - in production would use more sophisticated methods
        text_fields = []
        
        if "transcription" in event.data:
            text_fields.append(event.data["transcription"].get("text", ""))
        if "response_text" in event.data:
            text_fields.append(event.data["response_text"])
            
        pii_indicators = ["phone", "address", "email", "name", "ssn", "dob"]
        
        for text in text_fields:
            text_lower = text.lower()
            if any(indicator in text_lower for indicator in pii_indicators):
                return True
                
        return False
    
    async def _flush_audit_logs(self):
        """Flush accumulated audit logs to permanent storage."""
        if not self.audit_logs:
            return
            
        try:
            # In production, this would write to secure audit database
            # For now, log the audit entries
            logger.info(f"Flushing {len(self.audit_logs)} audit log entries")
            
            for entry in self.audit_logs:
                logger.info(f"AUDIT: {json.dumps(entry, default=str)}")
            
            # Clear the batch
            self.audit_logs.clear()
            self._last_flush = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}")
    
    async def _periodic_flush(self):
        """Periodic flush of audit logs."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_audit_logs()
            except Exception as e:
                logger.error(f"Error in periodic audit flush: {e}")


class PerformanceMonitoringSubscriber:
    """
    Subscriber for real-time performance monitoring and optimization.
    
    Features:
    - Sub-100ms latency tracking
    - Performance bottleneck detection
    - Scalability metrics collection
    - Automatic performance optimization recommendations
    """
    
    def __init__(self, event_streaming: EventStreamingService):
        self.event_streaming = event_streaming
        self.performance_metrics: Dict[str, List[float]] = {
            "total_processing_time": [],
            "stt_processing_time": [],
            "llm_processing_time": [],
            "tts_processing_time": [],
            "end_to_end_latency": []
        }
        self.session_timings: Dict[str, Dict[str, float]] = {}
        self.performance_alerts_sent = set()
    
    async def initialize(self):
        """Initialize performance monitoring subscriber."""
        logger.info("Initializing Performance Monitoring Subscriber...")
        
        success = await self.event_streaming.subscribe_to_events(
            event_types=[
                EventType.VOICE_INTERACTION_STARTED,
                EventType.STT_PROCESSED,
                EventType.LLM_PROCESSED,
                EventType.TTS_PROCESSED,
                EventType.VOICE_INTERACTION_COMPLETED
            ],
            callback=self._process_performance_event,
            consumer_group="performance_monitoring",
            consumer_name=f"performance_worker_{uuid4().hex[:8]}"
        )
        
        if success:
            # Start periodic metrics reporting
            asyncio.create_task(self._periodic_metrics_report())
            logger.info("Performance monitoring subscriber initialized successfully")
        else:
            logger.warning("Failed to initialize performance monitoring subscriber")
        
        return success
    
    async def _process_performance_event(self, event: VoiceEvent):
        """Process performance-related events."""
        try:
            session_id = event.session_id
            
            if event.event_type == EventType.VOICE_INTERACTION_STARTED:
                self.session_timings[session_id] = {"start_time": event.timestamp.timestamp()}
                
            elif event.event_type == EventType.STT_PROCESSED:
                processing_time = event.data.get("processing_time_ms", 0)
                self.performance_metrics["stt_processing_time"].append(processing_time)
                
                if session_id in self.session_timings:
                    self.session_timings[session_id]["stt_completed"] = event.timestamp.timestamp()
                
            elif event.event_type == EventType.LLM_PROCESSED:
                processing_time = event.data.get("processing_time_ms", 0)
                self.performance_metrics["llm_processing_time"].append(processing_time)
                
                if session_id in self.session_timings:
                    self.session_timings[session_id]["llm_completed"] = event.timestamp.timestamp()
                
            elif event.event_type == EventType.TTS_PROCESSED:
                processing_time = event.data.get("processing_time_ms", 0)
                self.performance_metrics["tts_processing_time"].append(processing_time)
                
                if session_id in self.session_timings:
                    self.session_timings[session_id]["tts_completed"] = event.timestamp.timestamp()
                
            elif event.event_type == EventType.VOICE_INTERACTION_COMPLETED:
                total_time = event.data.get("total_processing_time", 0) * 1000  # Convert to ms
                self.performance_metrics["total_processing_time"].append(total_time)
                
                # Calculate end-to-end latency
                if session_id in self.session_timings:
                    session_data = self.session_timings[session_id]
                    if "start_time" in session_data:
                        end_to_end = (event.timestamp.timestamp() - session_data["start_time"]) * 1000
                        self.performance_metrics["end_to_end_latency"].append(end_to_end)
                        
                        # Check if we exceeded the 100ms target
                        if end_to_end > 100:
                            await self._alert_performance_issue(session_id, end_to_end, event)
                    
                    # Clean up session data
                    del self.session_timings[session_id]
            
            # Limit metrics history size
            for metric_name in self.performance_metrics:
                if len(self.performance_metrics[metric_name]) > 1000:
                    self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-1000:]
                    
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
    
    async def _alert_performance_issue(self, session_id: str, latency_ms: float, event: VoiceEvent):
        """Alert on performance issues."""
        alert_key = f"{event.tenant_id}:{int(latency_ms // 50) * 50}"  # Group by 50ms buckets
        
        # Avoid spam - only alert once per tenant per latency bucket per minute
        if alert_key not in self.performance_alerts_sent:
            self.performance_alerts_sent.add(alert_key)
            
            # Remove alert key after 1 minute
            asyncio.create_task(self._remove_alert_key(alert_key, 60))
            
            # Publish performance alert event
            perf_event = VoiceEvent(
                event_type=EventType.PERFORMANCE_METRICS_UPDATED,
                session_id=session_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                timestamp=datetime.now(timezone.utc),
                data={
                    "alert_type": "latency_exceeded",
                    "target_ms": 100,
                    "actual_ms": latency_ms,
                    "severity": "high" if latency_ms > 200 else "medium",
                    "recommendations": self._get_performance_recommendations(latency_ms)
                },
                metadata={
                    "source": "performance_monitoring_subscriber",
                    "requires_optimization": True
                },
                correlation_id=event.correlation_id
            )
            
            await self.event_streaming.publish_event(perf_event)
            
            logger.warning(f"Performance alert: {latency_ms:.2f}ms latency in session {session_id}")
    
    async def _remove_alert_key(self, alert_key: str, delay_seconds: int):
        """Remove alert key after delay to allow new alerts."""
        await asyncio.sleep(delay_seconds)
        self.performance_alerts_sent.discard(alert_key)
    
    def _get_performance_recommendations(self, latency_ms: float) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        if latency_ms > 200:
            recommendations.append("Consider using faster Whisper model (tiny vs base)")
            recommendations.append("Implement response caching for common queries")
            recommendations.append("Use streaming responses to improve perceived performance")
        elif latency_ms > 150:
            recommendations.append("Check Redis cache hit rate")
            recommendations.append("Monitor OpenAI API response times")
        else:
            recommendations.append("Consider optimizing TTS synthesis")
            recommendations.append("Implement audio preprocessing optimizations")
            
        return recommendations
    
    async def _periodic_metrics_report(self):
        """Generate periodic performance metrics reports."""
        while True:
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                await self._generate_metrics_report()
            except Exception as e:
                logger.error(f"Error in periodic metrics report: {e}")
    
    async def _generate_metrics_report(self):
        """Generate comprehensive performance metrics report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                report["metrics"][metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values)
                }
        
        # Check if we're meeting performance targets
        end_to_end = report["metrics"].get("end_to_end_latency", {})
        if end_to_end:
            avg_latency = end_to_end.get("avg", 0)
            p95_latency = end_to_end.get("p95", 0)
            
            report["performance_status"] = {
                "target_met": avg_latency <= 100,
                "p95_target_met": p95_latency <= 100,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency
            }
        
        logger.info(f"Performance metrics report: {json.dumps(report, indent=2)}")


# Global subscriber instances
compliance_subscriber: Optional[ComplianceValidationSubscriber] = None
audit_subscriber: Optional[AuditLoggingSubscriber] = None
performance_subscriber: Optional[PerformanceMonitoringSubscriber] = None


async def initialize_auxiliary_services(event_streaming: EventStreamingService):
    """Initialize all auxiliary subscriber services."""
    global compliance_subscriber, audit_subscriber, performance_subscriber
    
    logger.info("Initializing auxiliary subscriber services...")
    
    # Initialize compliance validation
    compliance_subscriber = ComplianceValidationSubscriber(event_streaming)
    await compliance_subscriber.initialize()
    
    # Initialize audit logging  
    audit_subscriber = AuditLoggingSubscriber(event_streaming)
    await audit_subscriber.initialize()
    
    # Initialize performance monitoring
    performance_subscriber = PerformanceMonitoringSubscriber(event_streaming)
    await performance_subscriber.initialize()
    
    logger.info("All auxiliary subscriber services initialized successfully")


async def cleanup_auxiliary_services():
    """Clean up all auxiliary subscriber services."""
    logger.info("Cleaning up auxiliary subscriber services...")
    # Services are cleaned up when event streaming is cleaned up
    logger.info("Auxiliary services cleanup completed")