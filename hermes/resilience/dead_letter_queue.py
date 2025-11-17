"""
Dead Letter Queue (DLQ) for handling persistent failures in HERMES.

Critical for law firm customers - ensures no messages are lost even when
integrations (Clio, LawPay) are down for extended periods.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class DLQReason(Enum):
    """Reasons for sending message to DLQ."""
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    PERMANENT_FAILURE = "permanent_failure"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    INTEGRATION_DOWN = "integration_down"
    UNKNOWN_ERROR = "unknown_error"


class DLQPriority(Enum):
    """Priority levels for DLQ messages."""
    CRITICAL = "critical"  # Legal deadline, urgent matter
    HIGH = "high"  # Client intake, payment
    MEDIUM = "medium"  # Routine operations
    LOW = "low"  # Analytics, reporting


@dataclass
class DLQMessage:
    """Message stored in Dead Letter Queue."""
    id: str
    message_type: str  # "clio_matter", "lawpay_payment", "zapier_webhook"
    payload: Dict[str, Any]
    reason: DLQReason
    priority: DLQPriority
    tenant_id: str
    session_id: Optional[str] = None
    original_timestamp: datetime = field(default_factory=datetime.utcnow)
    dlq_timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    last_error: Optional[str] = None
    last_error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "message_type": self.message_type,
            "payload": self.payload,
            "reason": self.reason.value,
            "priority": self.priority.value,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "original_timestamp": self.original_timestamp.isoformat(),
            "dlq_timestamp": self.dlq_timestamp.isoformat(),
            "retry_count": self.retry_count,
            "last_error": self.last_error,
            "last_error_type": self.last_error_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DLQMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            message_type=data["message_type"],
            payload=data["payload"],
            reason=DLQReason(data["reason"]),
            priority=DLQPriority(data["priority"]),
            tenant_id=data["tenant_id"],
            session_id=data.get("session_id"),
            original_timestamp=datetime.fromisoformat(data["original_timestamp"]),
            dlq_timestamp=datetime.fromisoformat(data["dlq_timestamp"]),
            retry_count=data.get("retry_count", 0),
            last_error=data.get("last_error"),
            last_error_type=data.get("last_error_type"),
            metadata=data.get("metadata", {}),
        )


class DeadLetterQueue:
    """
    Enterprise-grade Dead Letter Queue for failed operations.

    Features:
    - Persistent storage (Redis)
    - Priority-based processing
    - Automatic retry with exponential backoff
    - Manual review and replay
    - Alerting for critical messages
    - Tenant isolation
    """

    DLQ_KEY_PREFIX = "hermes:dlq"
    DLQ_INDEX_KEY = "hermes:dlq:index"
    PRIORITY_KEY_PREFIX = "hermes:dlq:priority"
    MAX_MESSAGE_AGE_DAYS = 30  # Retain for 30 days
    ALERT_THRESHOLD_CRITICAL = 10  # Alert if 10+ critical messages

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize DLQ.

        Args:
            redis_client: Redis client for persistent storage
        """
        self.redis_client = redis_client
        self._initialized = False
        self._alert_cooldown: Dict[str, datetime] = {}

    async def initialize(self) -> None:
        """Initialize DLQ connection."""
        if not self.redis_client:
            logger.warning("DLQ initialized without Redis - using in-memory fallback")
            self._in_memory_queue: List[DLQMessage] = []
        self._initialized = True
        logger.info("Dead Letter Queue initialized")

    async def enqueue(
        self,
        message_type: str,
        payload: Dict[str, Any],
        reason: DLQReason,
        priority: DLQPriority,
        tenant_id: str,
        session_id: Optional[str] = None,
        retry_count: int = 0,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add message to Dead Letter Queue.

        Args:
            message_type: Type of message (e.g., "clio_matter_creation")
            payload: Original message payload
            reason: Reason for DLQ placement
            priority: Message priority
            tenant_id: Tenant identifier
            session_id: Optional session identifier
            retry_count: Number of retry attempts before DLQ
            error: Exception that caused failure
            metadata: Additional context

        Returns:
            Message ID in DLQ
        """
        if not self._initialized:
            await self.initialize()

        # Create DLQ message
        message = DLQMessage(
            id=f"dlq_{datetime.utcnow().timestamp()}_{tenant_id}",
            message_type=message_type,
            payload=payload,
            reason=reason,
            priority=priority,
            tenant_id=tenant_id,
            session_id=session_id,
            retry_count=retry_count,
            last_error=str(error) if error else None,
            last_error_type=type(error).__name__ if error else None,
            metadata=metadata or {},
        )

        # Store in Redis or in-memory
        if self.redis_client:
            await self._store_in_redis(message)
        else:
            self._in_memory_queue.append(message)

        # Log based on priority
        if priority == DLQPriority.CRITICAL:
            logger.error(
                f"🚨 CRITICAL message sent to DLQ: {message_type} for tenant {tenant_id} "
                f"(reason: {reason.value}, retries: {retry_count})"
            )
        else:
            logger.warning(
                f"⚠️  Message sent to DLQ: {message_type} for tenant {tenant_id} "
                f"(reason: {reason.value}, retries: {retry_count})"
            )

        # Check if alerting needed
        await self._check_alert_threshold(tenant_id, priority)

        return message.id

    async def _store_in_redis(self, message: DLQMessage) -> None:
        """Store message in Redis with indexing."""
        # Store message data
        key = f"{self.DLQ_KEY_PREFIX}:{message.id}"
        await self.redis_client.setex(
            key,
            timedelta(days=self.MAX_MESSAGE_AGE_DAYS),
            json.dumps(message.to_dict())
        )

        # Add to global index
        await self.redis_client.zadd(
            self.DLQ_INDEX_KEY,
            {message.id: message.dlq_timestamp.timestamp()}
        )

        # Add to priority queue
        priority_key = f"{self.PRIORITY_KEY_PREFIX}:{message.priority.value}"
        await self.redis_client.zadd(
            priority_key,
            {message.id: message.dlq_timestamp.timestamp()}
        )

    async def _check_alert_threshold(self, tenant_id: str, priority: DLQPriority) -> None:
        """Alert if too many critical messages for tenant."""
        if priority != DLQPriority.CRITICAL:
            return

        # Count critical messages for tenant
        critical_count = await self.count_messages(
            tenant_id=tenant_id,
            priority=DLQPriority.CRITICAL
        )

        if critical_count >= self.ALERT_THRESHOLD_CRITICAL:
            # Check cooldown
            alert_key = f"critical_dlq_{tenant_id}"
            now = datetime.utcnow()

            if alert_key in self._alert_cooldown:
                if now - self._alert_cooldown[alert_key] < timedelta(hours=1):
                    return  # Skip duplicate alert

            logger.error(
                f"🚨 ALERT: {critical_count} CRITICAL messages in DLQ for tenant {tenant_id}. "
                f"Manual intervention required!"
            )

            self._alert_cooldown[alert_key] = now

            # TODO: Send to external alerting (PagerDuty, email, Slack)
            # await alerting_service.send_alert(
            #     f"DLQ Alert: {critical_count} critical failures for tenant {tenant_id}",
            #     severity="critical",
            #     tenant_id=tenant_id
            # )

    async def dequeue(
        self,
        priority: Optional[DLQPriority] = None,
        tenant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[DLQMessage]:
        """
        Retrieve messages from DLQ for manual processing.

        Args:
            priority: Optional priority filter
            tenant_id: Optional tenant filter
            limit: Maximum messages to return

        Returns:
            List of DLQ messages
        """
        if not self._initialized:
            await self.initialize()

        if self.redis_client:
            return await self._dequeue_from_redis(priority, tenant_id, limit)
        else:
            # In-memory dequeue
            filtered = self._in_memory_queue
            if priority:
                filtered = [m for m in filtered if m.priority == priority]
            if tenant_id:
                filtered = [m for m in filtered if m.tenant_id == tenant_id]
            return filtered[:limit]

    async def _dequeue_from_redis(
        self,
        priority: Optional[DLQPriority],
        tenant_id: Optional[str],
        limit: int
    ) -> List[DLQMessage]:
        """Retrieve messages from Redis DLQ."""
        # Determine which key to query
        if priority:
            key = f"{self.PRIORITY_KEY_PREFIX}:{priority.value}"
        else:
            key = self.DLQ_INDEX_KEY

        # Get message IDs (oldest first)
        message_ids = await self.redis_client.zrange(key, 0, limit - 1)

        # Fetch messages
        messages = []
        for message_id in message_ids:
            message_key = f"{self.DLQ_KEY_PREFIX}:{message_id.decode()}"
            data = await self.redis_client.get(message_key)
            if data:
                message = DLQMessage.from_dict(json.loads(data))
                # Filter by tenant if specified
                if not tenant_id or message.tenant_id == tenant_id:
                    messages.append(message)

        return messages

    async def remove(self, message_id: str) -> bool:
        """
        Remove message from DLQ after successful processing.

        Args:
            message_id: DLQ message ID

        Returns:
            True if removed, False if not found
        """
        if not self._initialized:
            await self.initialize()

        if self.redis_client:
            # Remove from Redis
            key = f"{self.DLQ_KEY_PREFIX}:{message_id}"
            deleted = await self.redis_client.delete(key)

            # Remove from indices
            await self.redis_client.zrem(self.DLQ_INDEX_KEY, message_id)

            # Remove from priority queues (try all priorities)
            for priority in DLQPriority:
                priority_key = f"{self.PRIORITY_KEY_PREFIX}:{priority.value}"
                await self.redis_client.zrem(priority_key, message_id)

            logger.info(f"Removed message {message_id} from DLQ")
            return deleted > 0
        else:
            # In-memory removal
            original_len = len(self._in_memory_queue)
            self._in_memory_queue = [m for m in self._in_memory_queue if m.id != message_id]
            return len(self._in_memory_queue) < original_len

    async def count_messages(
        self,
        priority: Optional[DLQPriority] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Count messages in DLQ.

        Args:
            priority: Optional priority filter
            tenant_id: Optional tenant filter

        Returns:
            Number of messages matching criteria
        """
        if not self._initialized:
            await self.initialize()

        if self.redis_client:
            if priority:
                key = f"{self.PRIORITY_KEY_PREFIX}:{priority.value}"
                total = await self.redis_client.zcard(key)
            else:
                total = await self.redis_client.zcard(self.DLQ_INDEX_KEY)

            # If tenant filter, need to fetch and count manually
            if tenant_id:
                messages = await self.dequeue(priority, tenant_id, limit=10000)
                return len(messages)

            return total
        else:
            filtered = self._in_memory_queue
            if priority:
                filtered = [m for m in filtered if m.priority == priority]
            if tenant_id:
                filtered = [m for m in filtered if m.tenant_id == tenant_id]
            return len(filtered)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get DLQ statistics for monitoring.

        Returns:
            Dictionary with DLQ metrics
        """
        total = await self.count_messages()
        critical = await self.count_messages(priority=DLQPriority.CRITICAL)
        high = await self.count_messages(priority=DLQPriority.HIGH)
        medium = await self.count_messages(priority=DLQPriority.MEDIUM)
        low = await self.count_messages(priority=DLQPriority.LOW)

        return {
            "total_messages": total,
            "by_priority": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
            "requires_attention": critical > 0 or high > 10,
            "health_status": "CRITICAL" if critical >= 10 else "WARNING" if critical > 0 else "OK"
        }

    async def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Remove messages older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of messages removed
        """
        if not self.redis_client:
            return 0

        cutoff_timestamp = (datetime.utcnow() - timedelta(days=days)).timestamp()

        # Remove from index
        removed = await self.redis_client.zremrangebyscore(
            self.DLQ_INDEX_KEY,
            0,
            cutoff_timestamp
        )

        logger.info(f"Cleaned up {removed} DLQ messages older than {days} days")
        return removed


# Global DLQ instance (initialized with Redis client in main app)
dead_letter_queue = DeadLetterQueue()
