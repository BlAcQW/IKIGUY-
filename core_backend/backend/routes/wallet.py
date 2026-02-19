"""
Wallet API Routes for flow.ailabsafrica.com/billing

Provides endpoints for:
- Wallet balance management
- Deposits via multiple payment methods
- Payment method management
- Transaction history
- Webhooks from payment providers
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import logging

from ..auth import get_current_user_mongo, get_user_from_header
from ..mongo import get_database
from ..services.wallet_service import WalletService
from ..services.pdf_receipt_service import pdf_receipt_service
from ..models.wallet import (
    PaymentProvider,
    PaymentMethodType,
    Currency,
    TransactionType,
    TransactionStatus
)
from ..middleware.organization_context import (
    get_organization_context,
    get_user_organization_filter,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallet", tags=["Wallet & Billing"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DepositRequest(BaseModel):
    """Request to deposit funds."""
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: Currency = Field(Currency.USD, description="Currency")
    payment_method_id: str = Field(..., description="Payment method ID to use")
    description: Optional[str] = Field(None, description="Optional description")

    @validator("amount")
    def validate_amount(cls, v):
        """Validate amount is positive and has max 2 decimal places."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        if round(v, 2) != v:
            raise ValueError("Amount can have maximum 2 decimal places")
        return v


class AddPaymentMethodRequest(BaseModel):
    """Request to add payment method."""
    provider: PaymentProvider = Field(..., description="Payment provider")
    method_type: PaymentMethodType = Field(..., description="Payment method type")
    display_name: str = Field(..., description="Display name for method")

    # Card details (for Stripe/Flutterwave card)
    stripe_payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    flutterwave_token: Optional[str] = Field(None, description="Flutterwave tokenized card")

    # Mobile money details
    phone_number: Optional[str] = Field(None, description="Mobile money phone number")
    phone_network: Optional[str] = Field(None, description="Mobile network provider")

    # Bank details
    account_number: Optional[str] = Field(None, description="Bank account number")
    bank_name: Optional[str] = Field(None, description="Bank name")
    bank_code: Optional[str] = Field(None, description="Bank code")

    nickname: Optional[str] = Field(None, description="User nickname for method")

    @validator("phone_number")
    def validate_phone_number(cls, v, values):
        """Validate phone number if method type is mobile money."""
        if v and values.get("method_type") == PaymentMethodType.MOBILE_MONEY:
            # Remove spaces and dashes
            cleaned = v.replace(" ", "").replace("-", "")
            # Basic validation (should start with + or be 10+ digits)
            if not (cleaned.startswith("+") or len(cleaned) >= 10):
                raise ValueError("Invalid phone number format")
        return v


class UpdatePaymentMethodRequest(BaseModel):
    """Request to update payment method."""
    nickname: Optional[str] = Field(None, description="User nickname")
    is_default: Optional[bool] = Field(None, description="Set as default")


class UpdateWalletSettingsRequest(BaseModel):
    """Request to update wallet settings."""
    auto_reload_enabled: Optional[bool] = Field(None, description="Enable auto-reload")
    auto_reload_threshold: Optional[float] = Field(None, gt=0, description="Balance threshold for auto-reload")
    auto_reload_amount: Optional[float] = Field(None, gt=0, description="Amount to reload")
    auto_reload_payment_method_id: Optional[str] = Field(None, description="Payment method for auto-reload")
    low_balance_alert_enabled: Optional[bool] = Field(None, description="Enable low balance alerts")
    low_balance_threshold: Optional[float] = Field(None, gt=0, description="Alert threshold")


class PaymentMethodResponse(BaseModel):
    """Payment method response."""
    id: str
    provider: str
    method_type: str
    display_name: str
    nickname: Optional[str]
    is_default: bool
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    # Type-specific info
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    phone_number_masked: Optional[str] = None
    bank_name: Optional[str] = None


class WalletBalanceResponse(BaseModel):
    """Wallet balance response."""
    wallet_id: str
    balance: float
    pending_balance: float
    reserved_balance: float
    available_balance: float
    total_balance: float
    currency: str
    last_transaction_at: Optional[datetime]
    auto_reload_enabled: bool
    low_balance_alert_enabled: bool


class WalletSettingsResponse(BaseModel):
    """Wallet settings response."""
    wallet_id: str
    auto_reload_enabled: bool
    auto_reload_threshold: float
    auto_reload_amount: float
    auto_reload_payment_method_id: Optional[str]
    low_balance_alert_enabled: bool
    low_balance_threshold: float


class TransactionResponse(BaseModel):
    """Transaction response."""
    id: str
    transaction_type: str
    status: str
    amount: float
    currency: str
    processing_fee: float
    total_amount: float
    description: str
    payment_method_display: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class AvailablePaymentProvidersResponse(BaseModel):
    """Available payment providers response."""
    providers: List[Dict[str, Any]]


# ============================================================================
# DEPENDENCY: Get Wallet Service
# ============================================================================

async def get_wallet_service(db=Depends(get_database)) -> WalletService:
    """Get wallet service instance."""
    return WalletService(db)


# ============================================================================
# WALLET BALANCE ENDPOINTS
# ============================================================================

@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    request: Request,
    currency: Currency = Currency.USD,
    current_user: Dict = Depends(get_user_from_header),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get wallet balance for current user.

    Returns current balance, pending balance, and available balance.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # JWT tokens use "sub" for user ID, or "user_id"
        user_id = current_user.get("sub") or current_user.get("user_id")

        # Get or create wallet with organization context
        wallet = await wallet_service.get_or_create_wallet(user_id, currency, organization_id=org_id)

        return WalletBalanceResponse(
            wallet_id=wallet.id,
            balance=float(wallet.balance),
            pending_balance=float(wallet.pending_balance),
            reserved_balance=float(wallet.reserved_balance),
            available_balance=float(wallet.available_balance),
            total_balance=float(wallet.total_balance),
            currency=wallet.currency.value,
            last_transaction_at=wallet.last_transaction_at,
            auto_reload_enabled=wallet.auto_reload_enabled,
            low_balance_alert_enabled=wallet.low_balance_alert_enabled
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=WalletSettingsResponse)
async def get_wallet_settings(
    request: Request,
    currency: Currency = Currency.USD,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get wallet settings for current user.

    Returns auto-reload and alert settings.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")
        wallet = await wallet_service.get_or_create_wallet(user_id, currency, organization_id=org_id)

        return WalletSettingsResponse(
            wallet_id=wallet.id,
            auto_reload_enabled=wallet.auto_reload_enabled,
            auto_reload_threshold=float(wallet.auto_reload_threshold),
            auto_reload_amount=float(wallet.auto_reload_amount),
            auto_reload_payment_method_id=wallet.auto_reload_payment_method_id,
            low_balance_alert_enabled=wallet.low_balance_alert_enabled,
            low_balance_threshold=float(wallet.low_balance_threshold)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get wallet settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/settings", response_model=WalletSettingsResponse)
async def update_wallet_settings(
    http_request: Request,
    request: UpdateWalletSettingsRequest,
    currency: Currency = Currency.USD,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Update wallet settings for current user.

    Configure auto-reload and low balance alerts.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")
        wallet = await wallet_service.get_or_create_wallet(user_id, currency, organization_id=org_id)

        # Update only provided fields
        update_data = {}
        if request.auto_reload_enabled is not None:
            update_data["auto_reload_enabled"] = request.auto_reload_enabled
        if request.auto_reload_threshold is not None:
            update_data["auto_reload_threshold"] = Decimal(str(request.auto_reload_threshold))
        if request.auto_reload_amount is not None:
            update_data["auto_reload_amount"] = Decimal(str(request.auto_reload_amount))
        if request.auto_reload_payment_method_id is not None:
            # Validate payment method exists and belongs to user
            if request.auto_reload_payment_method_id:
                methods = await wallet_service.get_payment_methods(user_id)
                if not any(m.id == request.auto_reload_payment_method_id for m in methods):
                    raise HTTPException(status_code=400, detail="Invalid payment method ID")
            update_data["auto_reload_payment_method_id"] = request.auto_reload_payment_method_id
        if request.low_balance_alert_enabled is not None:
            update_data["low_balance_alert_enabled"] = request.low_balance_alert_enabled
        if request.low_balance_threshold is not None:
            update_data["low_balance_threshold"] = Decimal(str(request.low_balance_threshold))

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update wallet in database
        update_data["updated_at"] = datetime.utcnow()
        db = wallet_service.db
        await db.wallets.update_one(
            {"id": wallet.id},
            {"$set": update_data}
        )

        # Fetch updated wallet
        updated_wallet = await wallet_service.get_or_create_wallet(user_id, currency)

        logger.info(f"Updated wallet settings for user {user_id}: {update_data}")

        return WalletSettingsResponse(
            wallet_id=updated_wallet.id,
            auto_reload_enabled=updated_wallet.auto_reload_enabled,
            auto_reload_threshold=float(updated_wallet.auto_reload_threshold),
            auto_reload_amount=float(updated_wallet.auto_reload_amount),
            auto_reload_payment_method_id=updated_wallet.auto_reload_payment_method_id,
            low_balance_alert_enabled=updated_wallet.low_balance_alert_enabled,
            low_balance_threshold=float(updated_wallet.low_balance_threshold)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update wallet settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PAYMENT METHODS ENDPOINTS
# ============================================================================

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    request: Request,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get all payment methods for current user.

    Returns list of saved cards, mobile money accounts, etc.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")
        methods = await wallet_service.get_payment_methods(user_id, organization_id=org_id)

        return [
            PaymentMethodResponse(
                id=method.id,
                provider=method.provider.value,
                method_type=method.method_type.value,
                display_name=method.display_name,
                nickname=method.nickname,
                is_default=method.is_default,
                is_verified=method.is_verified,
                is_active=method.is_active,
                created_at=method.created_at,
                last_used_at=method.last_used_at,
                card_last4=method.card_last4,
                card_brand=method.card_brand,
                phone_number_masked=_mask_phone_number(method.phone_number) if method.phone_number else None,
                bank_name=method.bank_name
            )
            for method in methods
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    http_request: Request,
    request: AddPaymentMethodRequest,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Add new payment method.

    Supports:
    - Cards (Stripe, Flutterwave)
    - Mobile Money (MTN, Vodafone, AirtelTigo, M-Pesa)
    - Bank accounts

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        # Build payment method data
        method_data = {
            "user_id": user_id,
            "organization_id": org_id,
            "provider": request.provider,
            "method_type": request.method_type,
            "display_name": request.display_name,
            "nickname": request.nickname
        }

        # Add provider-specific data
        if request.stripe_payment_method_id:
            method_data["provider_payment_method_id"] = request.stripe_payment_method_id

        if request.flutterwave_token:
            method_data["provider_payment_method_id"] = request.flutterwave_token

        if request.phone_number:
            method_data["phone_number"] = request.phone_number

        if request.account_number:
            method_data["account_number"] = request.account_number
            method_data["bank_name"] = request.bank_name

        # Create payment method
        method = await wallet_service.add_payment_method(**method_data)

        return PaymentMethodResponse(
            id=method.id,
            provider=method.provider.value,
            method_type=method.method_type.value,
            display_name=method.display_name,
            nickname=method.nickname,
            is_default=method.is_default,
            is_verified=method.is_verified,
            is_active=method.is_active,
            created_at=method.created_at,
            last_used_at=method.last_used_at,
            card_last4=method.card_last4,
            card_brand=method.card_brand,
            phone_number_masked=_mask_phone_number(method.phone_number) if method.phone_number else None,
            bank_name=method.bank_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add payment method: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/payment-methods/{payment_method_id}")
async def update_payment_method(
    http_request: Request,
    payment_method_id: str,
    request: UpdatePaymentMethodRequest,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Update payment method (set as default, change nickname).

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        if request.is_default:
            await wallet_service.set_default_payment_method(user_id, payment_method_id, organization_id=org_id)

        return {"success": True, "message": "Payment method updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update payment method: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    http_request: Request,
    payment_method_id: str,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Delete payment method.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        # Soft delete by marking as inactive with org filter
        db = await get_database()
        query = {"id": payment_method_id, "user_id": user_id}
        if org_id:
            query["organization_id"] = org_id

        result = await db.payment_methods.update_one(
            query,
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Payment method not found")

        return {"success": True, "message": "Payment method deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete payment method: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DEPOSIT ENDPOINTS
# ============================================================================

@router.post("/deposit", response_model=TransactionResponse)
async def create_deposit(
    http_request: Request,
    request: DepositRequest,
    current_user: Dict = Depends(get_user_from_header),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Create deposit transaction.

    Initiates payment with selected payment provider.
    User will need to complete payment (e.g., enter PIN for mobile money).

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        # Create deposit transaction with organization context
        transaction = await wallet_service.create_deposit(
            user_id=user_id,
            amount=Decimal(str(request.amount)),
            currency=request.currency,
            payment_method_id=request.payment_method_id,
            description=request.description,
            organization_id=org_id
        )

        return TransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type.value,
            status=transaction.status.value,
            amount=float(transaction.amount),
            currency=transaction.currency.value,
            processing_fee=float(transaction.processing_fee),
            total_amount=float(transaction.total_amount),
            description=transaction.description,
            payment_method_display=None,  # TODO: Get from payment method
            created_at=transaction.created_at,
            completed_at=transaction.completed_at
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create deposit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRANSACTION HISTORY ENDPOINTS
# ============================================================================

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transaction_history(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict = Depends(get_user_from_header),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get transaction history for current user.

    Returns list of deposits, withdrawals, and usage charges.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")
        transactions = await wallet_service.get_transaction_history(user_id, limit, offset, organization_id=org_id)

        return [
            TransactionResponse(
                id=tx.id,
                transaction_type=tx.transaction_type.value,
                status=tx.status.value,
                amount=float(tx.amount),
                currency=tx.currency.value,
                processing_fee=float(tx.processing_fee),
                total_amount=float(tx.total_amount),
                description=tx.description,
                payment_method_display=None,  # TODO: Get from payment method
                created_at=tx.created_at,
                completed_at=tx.completed_at
            )
            for tx in transactions
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    request: Request,
    transaction_id: str,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get specific transaction details.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")
        transaction = await wallet_service.get_transaction(transaction_id, organization_id=org_id)

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Verify user owns this transaction and organization matches
        if transaction.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if org_id and hasattr(transaction, 'organization_id') and transaction.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return TransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type.value,
            status=transaction.status.value,
            amount=float(transaction.amount),
            currency=transaction.currency.value,
            processing_fee=float(transaction.processing_fee),
            total_amount=float(transaction.total_amount),
            description=transaction.description,
            payment_method_display=None,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}/receipt")
async def download_transaction_receipt(
    request: Request,
    transaction_id: str,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Generate and download PDF receipt for a transaction.

    Returns PDF file as downloadable attachment.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        from fastapi.responses import Response

        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        # Get transaction with organization context
        transaction = await wallet_service.get_transaction(transaction_id, organization_id=org_id)

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Verify user owns this transaction and organization matches
        if transaction.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if org_id and hasattr(transaction, 'organization_id') and transaction.organization_id != org_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get user email
        db = await get_database()
        user_doc = await db.users.find_one({"user_id": user_id})
        user_email = user_doc.get("email", "N/A") if user_doc else "N/A"

        # Get payment method display name
        payment_method_display = "N/A"
        if transaction.payment_method_id:
            payment_method_doc = await db.payment_methods.find_one({"id": transaction.payment_method_id})
            if payment_method_doc:
                payment_method_display = payment_method_doc.get("display_name", "N/A")

        # Prepare transaction data for PDF
        transaction_data = {
            "id": transaction.id,
            "transaction_type": transaction.transaction_type.value,
            "status": transaction.status.value,
            "amount": float(transaction.amount),
            "currency": transaction.currency.value,
            "processing_fee": float(transaction.processing_fee),
            "total_amount": float(transaction.total_amount),
            "description": transaction.description,
            "payment_method_display": payment_method_display,
            "created_at": transaction.created_at.isoformat(),
            "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
            "user_email": user_email,
            "balance_before": float(transaction.balance_before),
            "balance_after": float(transaction.balance_after)
        }

        # Generate PDF
        pdf_bytes = await pdf_receipt_service.generate_transaction_receipt(transaction_data)

        # Return PDF as download
        filename = f"receipt_{transaction_id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate receipt: {str(e)}")


# ============================================================================
# PAYMENT PROVIDER INFO ENDPOINTS
# ============================================================================

@router.get("/providers", response_model=AvailablePaymentProvidersResponse)
async def get_available_payment_providers(
    request: Request,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Get available payment providers and their supported methods.

    Returns information about Stripe, Flutterwave, Mobile Money, etc.

    Now properly scoped to organization. Requires authentication.
    """
    # Get and validate organization context
    org_id = get_organization_context(request)
    if org_id:
        await validate_organization_access(request, current_user, org_id)

    logger.info(f"Getting payment providers for organization: {org_id}")

    providers = [
        {
            "provider": "stripe",
            "name": "Stripe",
            "methods": ["card"],
            "currencies": ["USD", "EUR", "GBP", "GHS"],
            "countries": ["worldwide"],
            "logo_url": "/assets/logos/stripe.svg"
        },
        {
            "provider": "flutterwave",
            "name": "Flutterwave",
            "methods": ["card", "mobile_money", "bank_transfer"],
            "currencies": ["USD", "GHS", "NGN", "KES", "ZAR"],
            "countries": ["NG", "GH", "KE", "ZA", "UG", "TZ"],
            "logo_url": "/assets/logos/flutterwave.svg"
        },
        {
            "provider": "mtn_momo",
            "name": "MTN Mobile Money",
            "methods": ["mobile_money"],
            "currencies": ["GHS"],
            "countries": ["GH"],
            "logo_url": "/assets/logos/mtn.svg"
        },
        {
            "provider": "vodafone_cash",
            "name": "Vodafone Cash",
            "methods": ["mobile_money"],
            "currencies": ["GHS"],
            "countries": ["GH"],
            "logo_url": "/assets/logos/vodafone.svg"
        },
        {
            "provider": "airteltigo_money",
            "name": "AirtelTigo Money",
            "methods": ["mobile_money"],
            "currencies": ["GHS"],
            "countries": ["GH"],
            "logo_url": "/assets/logos/airteltigo.svg"
        },
        {
            "provider": "mpesa",
            "name": "M-Pesa",
            "methods": ["mobile_money"],
            "currencies": ["KES"],
            "countries": ["KE"],
            "logo_url": "/assets/logos/mpesa.svg"
        }
    ]

    return AvailablePaymentProvidersResponse(providers=providers)


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Handle Stripe webhook events.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        payload = await request.json()

        # Extract organization from webhook metadata
        metadata = payload.get("data", {}).get("object", {}).get("metadata", {})
        org_id = metadata.get("organization_id")

        logger.info(f"Stripe webhook received for organization: {org_id}, event: {payload.get('type')}")

        headers = dict(request.headers)

        result = await wallet_service.handle_webhook(
            provider=PaymentProvider.STRIPE,
            payload=payload,
            signature=stripe_signature,
            headers=headers
        )

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(
    request: Request,
    verif_hash: str = Header(None, alias="verif-hash"),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Handle Flutterwave webhook events.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        payload = await request.json()

        # Extract organization from webhook metadata
        metadata = payload.get("data", {}).get("meta", {})
        org_id = metadata.get("organization_id")

        logger.info(f"Flutterwave webhook received for organization: {org_id}, event: {payload.get('event')}")

        headers = dict(request.headers)

        result = await wallet_service.handle_webhook(
            provider=PaymentProvider.FLUTTERWAVE,
            payload=payload,
            signature=verif_hash,
            headers=headers
        )

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"Flutterwave webhook error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)


@router.post("/webhooks/momo-callback")
async def mobile_money_webhook(
    request: Request,
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Handle Mobile Money webhook events (MTN, Vodafone, AirtelTigo).

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        payload = await request.json()

        # Extract organization from webhook metadata
        metadata = payload.get("metadata", {})
        org_id = metadata.get("organization_id")

        # Detect provider from payload or headers
        provider = PaymentProvider.MTN_MOMO  # Default

        logger.info(f"Mobile Money webhook received for organization: {org_id}, provider: {provider}")

        headers = dict(request.headers)

        result = await wallet_service.handle_webhook(
            provider=provider,
            payload=payload,
            headers=headers
        )

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"Mobile Money webhook error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)


@router.post("/webhooks/mpesa-callback")
async def mpesa_webhook(
    request: Request,
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Handle M-Pesa webhook events.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        payload = await request.json()

        # Extract organization from webhook metadata
        metadata = payload.get("Body", {}).get("stkCallback", {}).get("CallbackMetadata", {})
        org_id = None
        # M-Pesa structure: look for organization_id in metadata items
        for item in metadata.get("Item", []):
            if item.get("Name") == "organization_id":
                org_id = item.get("Value")
                break

        logger.info(f"M-Pesa webhook received for organization: {org_id}, result: {payload.get('Body', {}).get('stkCallback', {}).get('ResultCode')}")

        headers = dict(request.headers)

        result = await wallet_service.handle_webhook(
            provider=PaymentProvider.MPESA,
            payload=payload,
            headers=headers
        )

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logger.error(f"M-Pesa webhook error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=400)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _mask_phone_number(phone: str) -> str:
    """
    Mask phone number for security.

    Example: +233244123456 -> +233****3456
    """
    if not phone or len(phone) < 8:
        return "****"

    # Keep country code and last 4 digits
    if phone.startswith("+"):
        country_code = phone[:4]
        last_digits = phone[-4:]
        masked_middle = "*" * (len(phone) - 8)
        return f"{country_code}{masked_middle}{last_digits}"
    else:
        last_digits = phone[-4:]
        masked_middle = "*" * (len(phone) - 4)
        return f"{masked_middle}{last_digits}"
