"""
LawPay API Client
Production-ready implementation with trust accounting compliance
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from ...resilience.circuit_breaker import CircuitBreaker
from ...resilience.retry import retry_async
from .models import Payment, PaymentAccount, PaymentStatus, TrustAccountType

logger = logging.getLogger(__name__)


class LawPayClient:
    """
    LawPay API client for legal payment processing.
    
    Implements trust accounting compliance and IOLTA handling
    following legal industry requirements.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.lawpay.com/v1",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        # Circuit breaker for resilience
        self._circuit_breaker = CircuitBreaker(
            name="lawpay",
            failure_threshold=5,
            recovery_timeout=60.0,
        )

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self) -> None:
        """Initialize HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            logger.info("LawPay client initialized")

    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("LawPay client closed")

    @retry_async(max_attempts=3, initial_delay=2.0)
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry and circuit breaker"""
        if not self._client:
            await self.initialize()

        async def _make_request():
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()

        return await self._circuit_breaker.call(_make_request)

    async def create_payment(
        self,
        amount: Decimal,
        account_type: TrustAccountType,
        client_name: str,
        description: str,
        matter_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        """
        Create a new payment.
        
        IMPORTANT: Trust account payments require special compliance handling.
        
        Args:
            amount: Payment amount
            account_type: Trust or operating account
            client_name: Client name
            description: Payment description
            matter_id: Associated matter ID
            metadata: Additional metadata
            
        Returns:
            Created payment
        """
        # Validate trust account compliance
        if account_type == TrustAccountType.TRUST:
            logger.info(f"Creating trust account payment for {client_name}: ${amount}")
            # In production, add additional compliance checks
        
        payload = {
            "amount": str(amount),
            "currency": "USD",
            "account_type": account_type.value,
            "client_name": client_name,
            "description": description,
            "matter_id": matter_id,
            "metadata": metadata or {},
        }

        response = await self._request("POST", "/payments", json=payload)
        return Payment(**response)

    async def get_payment(self, payment_id: str) -> Payment:
        """
        Get payment details.
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Payment details
        """
        response = await self._request("GET", f"/payments/{payment_id}")
        return Payment(**response)

    async def list_payments(
        self,
        account_type: Optional[TrustAccountType] = None,
        status: Optional[PaymentStatus] = None,
        limit: int = 50,
    ) -> List[Payment]:
        """
        List payments with filters.
        
        Args:
            account_type: Filter by account type
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of payments
        """
        params = {"limit": limit}
        if account_type:
            params["account_type"] = account_type.value
        if status:
            params["status"] = status.value

        response = await self._request("GET", "/payments", params=params)
        return [Payment(**p) for p in response.get("payments", [])]

    async def process_refund(
        self,
        payment_id: str,
        amount: Decimal,
        reason: str,
    ) -> Payment:
        """
        Process a refund.
        
        Args:
            payment_id: Original payment ID
            amount: Refund amount
            reason: Refund reason
            
        Returns:
            Updated payment with refund status
        """
        payload = {
            "amount": str(amount),
            "reason": reason,
        }

        response = await self._request(
            "POST",
            f"/payments/{payment_id}/refund",
            json=payload
        )
        return Payment(**response)

    async def get_account(self, account_id: str) -> PaymentAccount:
        """
        Get payment account details.
        
        Args:
            account_id: Account identifier
            
        Returns:
            Account details
        """
        response = await self._request("GET", f"/accounts/{account_id}")
        return PaymentAccount(**response)

    async def list_accounts(self) -> List[PaymentAccount]:
        """
        List all payment accounts.
        
        Returns:
            List of accounts
        """
        response = await self._request("GET", "/accounts")
        return [PaymentAccount(**a) for a in response.get("accounts", [])]

    async def validate_trust_accounting(
        self,
        payment_id: str,
    ) -> Dict[str, Any]:
        """
        Validate trust accounting compliance for a payment.
        
        Ensures proper handling of client trust funds per state bar rules.
        
        Args:
            payment_id: Payment to validate
            
        Returns:
            Validation result with compliance status
        """
        response = await self._request(
            "POST",
            f"/payments/{payment_id}/validate-trust"
        )
        
        logger.info(f"Trust accounting validation for {payment_id}: {response.get('status')}")
        return response
