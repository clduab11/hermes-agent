"""
Redis pub/sub event streaming for HERMES Hybrid Real-Time Orchestrator.
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

Implements asynchronous event streaming for auxiliary services including:
- Compliance validation
- Audit logging
- Knowledge graph updates
- Performance monitoring
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for voice pipeline streaming."""

    VOICE_INTERACTION_STARTED = "voice_interaction_started"
    VOICE_INTERACTION_COMPLETED = "voice_interaction_completed"
    STT_PROCESSED = "stt_processed"
    LLM_PROCESSED = "llm_processed"
    TTS_PROCESSED = "tts_processed"
    COMPLIANCE_CHECK_REQUIRED = "compliance_check_required"
    AUDIT_LOG_REQUIRED = "audit_log_required"
    KNOWLEDGE_UPDATE_REQUIRED = "knowledge_update_required"
    PERFORMANCE_METRICS_UPDATED = "performance_metrics_updated"
    ERROR_OCCURRED = "error_occurred"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_TERMINATED = "connection_terminated"


@dataclass
class VoiceEvent:
    """Standardized voice event for pub/sub streaming."""

    event_type: EventType
    session_id: str
    tenant_id: str
    user_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    correlation_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceEvent":
        """Create event from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            user_id=data.get("user_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            metadata=data["metadata"],
            correlation_id=data["correlation_id"],
        )


class EventStreamingService:
    """
    Redis-based event streaming service for real-time voice pipeline events.

    Features:
    - High-performance pub/sub with Redis Streams
    - Event filtering and routing
    - Tenant isolation for multi-tenant events
    - Automatic retry and error handling
    - Performance monitoring and metrics
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.active_subscriptions: Set[str] = set()
        self._subscriber_tasks: List[asyncio.Task] = []
        self._running = False

    async def initialize(self) -> bool:
        """Initialize Redis connection and event streaming."""
        try:
            # Initialize Redis client with asyncio support
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=1,  # Use separate DB for events
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Event streaming service initialized with Redis")
            self._running = True
            return True

        except Exception as e:
            logger.warning(f"Failed to initialize event streaming: {e}")
            self.redis_client = None
            return False

    async def cleanup(self):
        """Clean up event streaming resources."""
        self._running = False

        # Cancel all subscriber tasks
        for task in self._subscriber_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._subscriber_tasks.clear()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("Event streaming service cleanup completed")

    async def publish_event(self, event: VoiceEvent) -> bool:
        """
        Publish an event to the appropriate Redis streams.

        Args:
            event: Voice event to publish

        Returns:
            True if event was published successfully
        """
        if not self.redis_client or not self._running:
            logger.debug(
                f"Event streaming not available, skipping event: {event.event_type}"
            )
            return False

        try:
            # Create tenant-specific stream name for isolation
            stream_name = f"voice_events:{event.tenant_id}"

            # Publish to tenant-specific stream
            await self.redis_client.xadd(
                stream_name,
                event.to_dict(),
                maxlen=10000,  # Keep last 10K events per tenant
            )

            # Also publish to global event stream for system-wide monitoring
            global_stream = "voice_events:global"
            await self.redis_client.xadd(
                global_stream,
                {**event.to_dict(), "source_stream": stream_name},
                maxlen=50000,  # Keep last 50K global events
            )

            logger.debug(
                f"Published event {event.event_type} for session {event.session_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            return False

    async def subscribe_to_events(
        self,
        event_types: List[EventType],
        callback: Callable[[VoiceEvent], None],
        tenant_id: Optional[str] = None,
        consumer_group: str = "default",
        consumer_name: str = "worker",
    ) -> bool:
        """
        Subscribe to specific event types with callback processing.

        Args:
            event_types: List of event types to subscribe to
            callback: Async callback function to process events
            tenant_id: Optional tenant ID for tenant-specific events
            consumer_group: Redis consumer group name
            consumer_name: Consumer name within the group

        Returns:
            True if subscription was established successfully
        """
        if not self.redis_client or not self._running:
            logger.warning("Cannot subscribe: event streaming not available")
            return False

        # Determine stream names based on tenant filtering
        if tenant_id:
            stream_names = [f"voice_events:{tenant_id}"]
        else:
            stream_names = ["voice_events:global"]

        # Create consumer groups if they don't exist
        for stream_name in stream_names:
            try:
                await self.redis_client.xgroup_create(
                    stream_name, consumer_group, id="0", mkstream=True
                )
                logger.debug(
                    f"Created consumer group {consumer_group} for stream {stream_name}"
                )
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(f"Failed to create consumer group: {e}")
                    return False

        # Start subscriber task
        task = asyncio.create_task(
            self._event_subscriber_loop(
                stream_names, event_types, callback, consumer_group, consumer_name
            )
        )
        self._subscriber_tasks.append(task)

        subscription_key = f"{consumer_group}:{consumer_name}:{','.join(stream_names)}"
        self.active_subscriptions.add(subscription_key)

        logger.info(
            f"Subscribed to events {[et.value for et in event_types]} in streams {stream_names}"
        )
        return True

    async def _event_subscriber_loop(
        self,
        stream_names: List[str],
        event_types: List[EventType],
        callback: Callable[[VoiceEvent], None],
        consumer_group: str,
        consumer_name: str,
    ):
        """Internal event subscriber loop."""
        event_type_values = {et.value for et in event_types}

        while self._running and self.redis_client:
            try:
                # Read events from streams
                streams = {name: ">" for name in stream_names}
                events = await self.redis_client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    streams,
                    count=10,
                    block=1000,  # Block for 1 second
                )

                for stream_name, stream_events in events:
                    for event_id, event_data in stream_events:
                        try:
                            # Parse event
                            voice_event = VoiceEvent.from_dict(event_data)

                            # Filter by event type
                            if voice_event.event_type.value in event_type_values:
                                # Process event with callback
                                await callback(voice_event)

                                # Acknowledge successful processing
                                await self.redis_client.xack(
                                    stream_name, consumer_group, event_id
                                )

                        except Exception as e:
                            logger.error(f"Error processing event {event_id}: {e}")
                            # Don't acknowledge failed events for retry

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event subscriber loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def get_stream_info(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about event streams."""
        if not self.redis_client:
            return {"error": "Event streaming not available"}

        try:
            info = {
                "active_subscriptions": len(self.active_subscriptions),
                "running": self._running,
                "subscriber_tasks": len(self._subscriber_tasks),
            }

            # Get stream lengths
            if tenant_id:
                stream_name = f"voice_events:{tenant_id}"
                try:
                    info[f"stream_length_{tenant_id}"] = await self.redis_client.xlen(
                        stream_name
                    )
                except:
                    info[f"stream_length_{tenant_id}"] = 0
            else:
                # Get global stream info
                try:
                    info["global_stream_length"] = await self.redis_client.xlen(
                        "voice_events:global"
                    )
                except:
                    info["global_stream_length"] = 0

            return info

        except Exception as e:
            return {"error": f"Failed to get stream info: {e}"}


# Global event streaming service instance
event_streaming = EventStreamingService()
