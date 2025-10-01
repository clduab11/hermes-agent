"""
LawPay data models
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TrustAccountType(Enum):
    """Trust account types for legal payments"""
    TRUST = "trust"  # Client trust account (IOLTA)
    OPERATING = "operating"  # Law firm operating account


class PaymentStatus(Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentAccount(BaseModel):
    """Payment account information"""
    account_id: str
    account_type: TrustAccountType
    name: str
    last_four: Optional[str] = None
    balance: Optional[Decimal] = None


class Payment(BaseModel):
    """Payment transaction"""
    payment_id: Optional[str] = None
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD")
    account_type: TrustAccountType
    client_name: str
    matter_id: Optional[str] = None
    description: str
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RefundRequest(BaseModel):
    """Refund request"""
    payment_id: str
    amount: Decimal = Field(..., gt=0)
    reason: str
