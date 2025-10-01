"""
Test LawPay integration
"""

import os
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

import pytest
from unittest.mock import AsyncMock, Mock, patch
from decimal import Decimal

from hermes.integrations.lawpay.client import LawPayClient
from hermes.integrations.lawpay.models import Payment, PaymentStatus, TrustAccountType


class TestLawPayClient:
    """Test LawPay API client"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client can be initialized"""
        client = LawPayClient(api_key="test-key")
        await client.initialize()
        
        assert client._client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_create_payment(self):
        """Test payment creation"""
        client = LawPayClient(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payment_id": "pay_123",
                "amount": "1000.00",
                "currency": "USD",
                "account_type": "operating",
                "client_name": "John Doe",
                "description": "Legal fees",
                "status": "pending",
            }
            
            payment = await client.create_payment(
                amount=Decimal("1000.00"),
                account_type=TrustAccountType.OPERATING,
                client_name="John Doe",
                description="Legal fees"
            )
            
            assert payment.payment_id == "pay_123"
            assert payment.client_name == "John Doe"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_trust_account_payment(self):
        """Test trust account payment creation"""
        client = LawPayClient(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payment_id": "pay_124",
                "amount": "5000.00",
                "currency": "USD",
                "account_type": "trust",
                "client_name": "Jane Smith",
                "description": "Retainer",
                "status": "pending",
            }
            
            payment = await client.create_payment(
                amount=Decimal("5000.00"),
                account_type=TrustAccountType.TRUST,
                client_name="Jane Smith",
                description="Retainer"
            )
            
            assert payment.account_type == TrustAccountType.TRUST

    @pytest.mark.asyncio
    async def test_process_refund(self):
        """Test refund processing"""
        client = LawPayClient(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payment_id": "pay_123",
                "amount": "1000.00",
                "currency": "USD",
                "account_type": "operating",
                "client_name": "John Doe",
                "description": "Legal fees",
                "status": "refunded",
            }
            
            payment = await client.process_refund(
                payment_id="pay_123",
                amount=Decimal("1000.00"),
                reason="Client request"
            )
            
            assert payment.status == PaymentStatus.REFUNDED

    @pytest.mark.asyncio
    async def test_list_payments(self):
        """Test listing payments"""
        client = LawPayClient(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payments": [
                    {
                        "payment_id": "pay_1",
                        "amount": "100.00",
                        "currency": "USD",
                        "account_type": "operating",
                        "client_name": "Client 1",
                        "description": "Fee 1",
                        "status": "completed",
                    },
                    {
                        "payment_id": "pay_2",
                        "amount": "200.00",
                        "currency": "USD",
                        "account_type": "trust",
                        "client_name": "Client 2",
                        "description": "Fee 2",
                        "status": "pending",
                    }
                ]
            }
            
            payments = await client.list_payments(limit=10)
            
            assert len(payments) == 2
            assert payments[0].payment_id == "pay_1"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with LawPayClient(api_key="test-key") as client:
            assert client._client is not None
        
        assert client._client is None


class TestPaymentModels:
    """Test payment data models"""

    def test_payment_validation(self):
        """Test Payment model validation"""
        payment = Payment(
            amount=Decimal("1000.00"),
            account_type=TrustAccountType.OPERATING,
            client_name="Test Client",
            description="Test payment"
        )
        
        assert payment.amount == Decimal("1000.00")
        assert payment.status == PaymentStatus.PENDING
        assert payment.currency == "USD"

    def test_payment_amount_validation(self):
        """Test payment amount must be positive"""
        with pytest.raises(ValueError):
            Payment(
                amount=Decimal("-100.00"),
                account_type=TrustAccountType.OPERATING,
                client_name="Test",
                description="Test"
            )

    def test_trust_account_enum(self):
        """Test TrustAccountType enum"""
        assert TrustAccountType.TRUST.value == "trust"
        assert TrustAccountType.OPERATING.value == "operating"
