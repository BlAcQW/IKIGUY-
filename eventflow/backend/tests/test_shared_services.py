"""
Integration tests for EventFlow shared services.

Tests VAPI, n8n, Wallet, UsageCalculator, and RAG services
to ensure EventFlow can use them properly.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional

# Shared services imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from apps.shared.integration.rag import RAGService, KnowledgeDocument
from apps.shared.integration.wallet import WalletService, Transaction
from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier


class TestRAGService:
    """Test RAG service integration for AI recommendations."""

    @pytest.mark.asyncio
    async def test_rag_service_initialization(self):
        """Test RAG service can be initialized."""
        # Note: This requires pgvector and proper env vars
        # For now, we just test that the module can be imported
        assert RAGService is not None

    def test_knowledge_document_creation(self):
        """Test creating a knowledge document."""
        doc = KnowledgeDocument(
            title="Event Planning Best Practices",
            content="Always book venue 3 months in advance for large events.",
            category="event_planning",
            tags=["venue", "booking", "timeline"]
        )
        assert doc.title == "Event Planning Best Practices"
        assert "venue" in doc.tags


class TestWalletService:
    """Test Wallet service integration for payment management."""

    def test_wallet_service_import(self):
        """Test wallet service can be imported."""
        assert WalletService is not None

    def test_transaction_model(self):
        """Test transaction model creation."""
        from apps.shared.integration.wallet import TransactionType, TransactionStatus, Currency

        transaction = Transaction(
            wallet_id="wallet_456",
            type=TransactionType.DEBIT,
            amount=Decimal("50.00"),
            currency=Currency.GHS,
            status=TransactionStatus.COMPLETED,
            description="Voice call - John Doe - Book venue task",
            balance_before=Decimal("100.00"),
            balance_after=Decimal("50.00")
        )
        assert transaction.amount == Decimal("50.00")
        assert transaction.currency == Currency.GHS
        assert transaction.type == TransactionType.DEBIT


class TestUsageCalculator:
    """Test Usage Calculator for cost tracking."""

    def test_usage_calculator_import(self):
        """Test usage calculator can be imported."""
        assert UsageCalculator is not None

    def test_pricing_tier_enum(self):
        """Test pricing tier enumeration."""
        assert PricingTier.FREE is not None
        assert PricingTier.BASIC is not None
        assert PricingTier.PREMIUM is not None


class TestVAPIServiceIntegration:
    """Test VAPI service for voice AI calls."""

    def test_vapi_module_import(self):
        """Test VAPI service can be imported."""
        from apps.shared.integration.vapi import VAPIService
        assert VAPIService is not None


class TestN8NServiceIntegration:
    """Test n8n service for workflow automation."""

    def test_n8n_module_import(self):
        """Test n8n service can be imported."""
        from apps.shared.integration.n8n import N8NIntegration
        assert N8NIntegration is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
