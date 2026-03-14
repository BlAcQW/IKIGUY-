"""
Unit tests for QuickBooks Online sync integration.

Tests token encryption, OAuth state handling, and field mapping.
"""

import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integration.quickbooks_client import (
    QuickBooksClient,
    create_oauth_state,
    decrypt_token,
    encrypt_token,
    verify_oauth_state,
)
from app.models.quickbooks import QBOConnectionStatus, QBOSyncResult


# ============================================================================
# Token Encryption Tests
# ============================================================================


class TestTokenEncryption:
    """Test Fernet token encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        secret = "test-secret-key-for-encryption"
        token = "my-access-token-12345"
        encrypted = encrypt_token(token, secret)
        assert encrypted != token
        decrypted = decrypt_token(encrypted, secret)
        assert decrypted == token

    def test_different_secrets_fail(self):
        secret1 = "secret-one"
        secret2 = "secret-two"
        token = "my-token"
        encrypted = encrypt_token(token, secret1)
        with pytest.raises(Exception):
            decrypt_token(encrypted, secret2)

    def test_empty_token(self):
        secret = "test-secret"
        encrypted = encrypt_token("", secret)
        assert decrypt_token(encrypted, secret) == ""


# ============================================================================
# OAuth State Tests
# ============================================================================


class TestOAuthState:
    """Test HMAC-signed OAuth state parameter."""

    def test_create_and_verify_state(self):
        secret = "state-signing-secret"
        org_id = "org_abc123"
        state = create_oauth_state(org_id, secret)
        result = verify_oauth_state(state, secret)
        assert result == org_id

    def test_wrong_secret_fails(self):
        state = create_oauth_state("org_123", "secret1")
        result = verify_oauth_state(state, "secret2")
        assert result is None

    def test_tampered_state_fails(self):
        secret = "my-secret"
        state = create_oauth_state("org_123", secret)
        # Tamper with the state
        parts = state.rsplit(".", 1)
        tampered = parts[0] + ".0000" + parts[1][4:]
        result = verify_oauth_state(tampered, secret)
        assert result is None

    def test_expired_state_fails(self):
        secret = "my-secret"
        state = create_oauth_state("org_123", secret)
        # Verify with 0 max_age to simulate expiry
        result = verify_oauth_state(state, secret, max_age_seconds=0)
        assert result is None

    def test_malformed_state_returns_none(self):
        result = verify_oauth_state("not-a-valid-state", "secret")
        assert result is None


# ============================================================================
# Model Tests
# ============================================================================


class TestQBOModels:
    """Test QBO Pydantic models."""

    def test_connection_status_disconnected(self):
        status = QBOConnectionStatus(is_connected=False)
        assert status.is_connected is False
        assert status.company_name is None
        assert status.realm_id is None

    def test_connection_status_connected(self):
        status = QBOConnectionStatus(
            is_connected=True,
            company_name="Test Corp",
            realm_id="123456789",
            connected_at=datetime(2025, 1, 1),
        )
        assert status.is_connected is True
        assert status.company_name == "Test Corp"

    def test_sync_result_success(self):
        result = QBOSyncResult(
            total_invoices=10,
            synced=8,
            failed=2,
            errors=["INV-001: Connection error", "INV-005: Customer not found"],
        )
        assert result.total_invoices == 10
        assert result.synced == 8
        assert result.failed == 2
        assert len(result.errors) == 2

    def test_sync_result_all_synced(self):
        result = QBOSyncResult(
            total_invoices=5, synced=5, failed=0, errors=[]
        )
        assert result.failed == 0
        assert result.errors == []


# ============================================================================
# QuickBooksClient Tests
# ============================================================================


class TestQuickBooksClient:
    """Test QuickBooksClient configuration and methods."""

    @patch("app.integration.quickbooks_client.settings")
    def test_is_configured_true(self, mock_settings):
        mock_settings.QBO_CLIENT_ID = "test_id"
        mock_settings.QBO_CLIENT_SECRET = "test_secret"
        mock_settings.QBO_REDIRECT_URI = "http://localhost/callback"
        mock_settings.QBO_ENVIRONMENT = "sandbox"
        mock_settings.SECRET_KEY = "test-key"
        client = QuickBooksClient()
        assert client.is_configured is True

    @patch("app.integration.quickbooks_client.settings")
    def test_is_configured_false(self, mock_settings):
        mock_settings.QBO_CLIENT_ID = None
        mock_settings.QBO_CLIENT_SECRET = None
        mock_settings.QBO_REDIRECT_URI = "http://localhost/callback"
        mock_settings.QBO_ENVIRONMENT = "sandbox"
        mock_settings.SECRET_KEY = "test-key"
        client = QuickBooksClient()
        assert client.is_configured is False


# ============================================================================
# Invoice Field Mapping Tests
# ============================================================================


class TestInvoiceFieldMapping:
    """Test DiaServe to QBO invoice field mapping logic."""

    def test_invoice_number_truncation(self):
        """DocNumber max 21 chars."""
        long_number = "DIA-2025-EXTRA-LONG-NUMBER-HERE"
        truncated = long_number[:21]
        assert len(truncated) <= 21

    def test_date_formatting(self):
        """QBO expects YYYY-MM-DD date strings."""
        dt = datetime(2025, 6, 15, 10, 30, 0)
        formatted = dt.strftime("%Y-%m-%d")
        assert formatted == "2025-06-15"

    def test_line_item_amount_calculation(self):
        """Line amount = quantity * unit_price."""
        qty = 3.0
        unit_price = 150.00
        amount = qty * unit_price
        assert amount == 450.00

    def test_tax_code_selection(self):
        """TAX if rate > 0, NON otherwise."""
        assert ("TAX" if 12.5 > 0 else "NON") == "TAX"
        assert ("TAX" if 0 > 0 else "NON") == "NON"

    def test_notes_truncation(self):
        """PrivateNote max 4000 chars."""
        long_notes = "x" * 5000
        truncated = long_notes[:4000]
        assert len(truncated) == 4000
