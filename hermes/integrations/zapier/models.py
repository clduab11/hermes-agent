"""
Zapier webhook data models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl


class EventType(Enum):
    """Available webhook event types"""
    MATTER_CREATED = "matter.created"
    MATTER_UPDATED = "matter.updated"
    CLIENT_CONTACTED = "client.contacted"
    INTAKE_COMPLETED = "intake.completed"
    PAYMENT_RECEIVED = "payment.received"
    DOCUMENT_UPLOADED = "document.uploaded"


class WebhookSubscription(BaseModel):
    """Webhook subscription"""
    subscription_id: Optional[str] = None
    target_url: HttpUrl
    event_type: EventType
    active: bool = True
    created_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookEvent(BaseModel):
    """Webhook event payload"""
    event_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
