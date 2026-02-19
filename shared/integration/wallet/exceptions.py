"""
Custom exceptions for wallet system.

Provides specific exception types for better error handling and clearer error messages.

Author: KasaAI Team
Date: 2025-10-27
"""


class WalletError(Exception):
    """Base exception for all wallet-related errors."""
    pass


class WalletNotFoundError(WalletError):
    """Raised when wallet is not found."""

    def __init__(self, wallet_id: str = None, user_id: str = None):
        if wallet_id:
            message = f"Wallet {wallet_id} not found"
        elif user_id:
            message = f"No wallet found for user {user_id}"
        else:
            message = "Wallet not found"
        super().__init__(message)


class InsufficientBalanceError(WalletError):
    """Raised when wallet has insufficient balance for operation."""

    def __init__(self, available: float, required: float):
        message = f"Insufficient balance. Available: {available}, Required: {required}"
        super().__init__(message)
        self.available = available
        self.required = required


class DuplicateTransactionError(WalletError):
    """Raised when attempting to create a duplicate transaction (idempotency key exists)."""

    def __init__(self, idempotency_key: str):
        message = f"Transaction with idempotency key '{idempotency_key}' already exists"
        super().__init__(message)
        self.idempotency_key = idempotency_key


class TransactionNotFoundError(WalletError):
    """Raised when transaction is not found."""

    def __init__(self, transaction_id: str):
        message = f"Transaction {transaction_id} not found"
        super().__init__(message)
        self.transaction_id = transaction_id


class WalletSuspendedError(WalletError):
    """Raised when attempting operations on a suspended wallet."""

    def __init__(self, wallet_id: str):
        message = f"Wallet {wallet_id} is suspended and cannot process transactions"
        super().__init__(message)
        self.wallet_id = wallet_id


class WalletClosedError(WalletError):
    """Raised when attempting operations on a closed wallet."""

    def __init__(self, wallet_id: str):
        message = f"Wallet {wallet_id} is closed and cannot be used"
        super().__init__(message)
        self.wallet_id = wallet_id


class PaymentMethodNotFoundError(WalletError):
    """Raised when payment method is not found."""

    def __init__(self, payment_method_id: str):
        message = f"Payment method {payment_method_id} not found"
        super().__init__(message)
        self.payment_method_id = payment_method_id


class PaymentMethodNotVerifiedError(WalletError):
    """Raised when attempting to use unverified payment method."""

    def __init__(self, payment_method_id: str):
        message = f"Payment method {payment_method_id} is not verified"
        super().__init__(message)
        self.payment_method_id = payment_method_id


class ProviderError(WalletError):
    """Base exception for payment provider errors."""
    pass


class ProviderNotConfiguredError(ProviderError):
    """Raised when payment provider is not configured."""

    def __init__(self, provider: str):
        message = f"Payment provider '{provider}' is not configured or not active"
        super().__init__(message)
        self.provider = provider


class ProviderAPIError(ProviderError):
    """Raised when provider API returns an error."""

    def __init__(self, provider: str, error_message: str, error_code: str = None):
        message = f"Provider {provider} error: {error_message}"
        if error_code:
            message += f" (code: {error_code})"
        super().__init__(message)
        self.provider = provider
        self.error_message = error_message
        self.error_code = error_code


class PaymentDeclinedError(ProviderError):
    """Raised when payment is declined by provider."""

    def __init__(self, provider: str, reason: str):
        message = f"Payment declined by {provider}: {reason}"
        super().__init__(message)
        self.provider = provider
        self.reason = reason


class InvalidWebhookSignatureError(ProviderError):
    """Raised when webhook signature verification fails."""

    def __init__(self, provider: str):
        message = f"Invalid webhook signature from {provider}"
        super().__init__(message)
        self.provider = provider


class RefundError(WalletError):
    """Raised when refund operation fails."""

    def __init__(self, transaction_id: str, reason: str):
        message = f"Cannot refund transaction {transaction_id}: {reason}"
        super().__init__(message)
        self.transaction_id = transaction_id
        self.reason = reason


class FraudDetectionError(WalletError):
    """Raised when transaction is blocked by fraud detection."""

    def __init__(self, reason: str, rule: str = None):
        message = f"Transaction blocked by fraud detection: {reason}"
        if rule:
            message += f" (rule: {rule})"
        super().__init__(message)
        self.reason = reason
        self.rule = rule


class ValidationError(WalletError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        full_message = f"Validation error for '{field}': {message}"
        super().__init__(full_message)
        self.field = field
        self.validation_message = message


class ConfigurationError(WalletError):
    """Raised when there's a configuration problem."""

    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")


class DatabaseError(WalletError):
    """Raised when database operation fails."""

    def __init__(self, operation: str, details: str = None):
        message = f"Database error during {operation}"
        if details:
            message += f": {details}"
        super().__init__(message)
        self.operation = operation
        self.details = details
