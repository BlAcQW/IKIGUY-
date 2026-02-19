"""
Wallet Service for KasaAI Core Backend.

Comprehensive wallet management with support for:
- Flutterwave
- Stripe
- Mobile Money (MTN, Vodafone, AirtelTigo)
- M-Pesa (Kenya)
- Bank transfers
"""

import logging
import asyncio
import hashlib
import hmac
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models.wallet import (
    Wallet,
    Transaction,
    PaymentMethod,
    WebhookEvent,
    ProviderConfig,
    PaymentProvider,
    PaymentMethodType,
    TransactionType,
    TransactionStatus,
    Currency
)
from .payment_providers.stripe_client import StripeClient
from .wallet_notifications import wallet_notification_service

logger = logging.getLogger(__name__)


class WalletService:
    """
    Service for comprehensive wallet and payment management.

    Supports multiple payment providers and methods including:
    - Card payments (Stripe, Flutterwave)
    - Mobile Money (MTN, Vodafone, AirtelTigo, M-Pesa)
    - Bank transfers
    - Digital wallets
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize wallet service.

        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.wallets = db.wallets
        self.transactions = db.transactions
        self.payment_methods = db.payment_methods
        self.webhook_events = db.webhook_events
        self.provider_configs = db.provider_configs

        # HTTP client for API requests
        self.http_client = httpx.AsyncClient(timeout=30.0)

    # ============================================================================
    # WALLET MANAGEMENT
    # ============================================================================

    async def get_or_create_wallet(
        self,
        user_id: str,
        currency: Currency = Currency.USD,
        tenant_id: Optional[str] = None
    ) -> Wallet:
        """
        Get existing wallet or create new one.

        Args:
            user_id: User ID
            currency: Wallet currency
            tenant_id: Optional tenant ID

        Returns:
            Wallet instance
        """
        # Check for existing wallet
        wallet_doc = await self.wallets.find_one({
            "user_id": user_id,
            "currency": currency.value,
            "is_active": True
        })

        if wallet_doc:
            return Wallet(**wallet_doc)

        # Create new wallet
        wallet = Wallet(
            user_id=user_id,
            tenant_id=tenant_id,
            currency=currency,
            balance=Decimal("0.00"),
            pending_balance=Decimal("0.00"),
            reserved_balance=Decimal("0.00")
        )

        await self.wallets.insert_one(wallet.dict())
        logger.info(f"Created new wallet {wallet.id} for user {user_id}")

        return wallet

    async def get_wallet_balance(self, user_id: str, currency: Currency = Currency.USD) -> Dict[str, Any]:
        """
        Get wallet balance information.

        Args:
            user_id: User ID
            currency: Wallet currency

        Returns:
            Balance information dict
        """
        wallet = await self.get_or_create_wallet(user_id, currency)

        return {
            "wallet_id": wallet.id,
            "balance": float(wallet.balance),
            "pending_balance": float(wallet.pending_balance),
            "reserved_balance": float(wallet.reserved_balance),
            "available_balance": float(wallet.available_balance),
            "total_balance": float(wallet.total_balance),
            "currency": wallet.currency.value,
            "last_transaction_at": wallet.last_transaction_at.isoformat() if wallet.last_transaction_at else None
        }

    async def update_wallet_balance(
        self,
        wallet_id: str,
        amount: Decimal,
        transaction_type: str
    ) -> Wallet:
        """
        Update wallet balance after transaction.

        Args:
            wallet_id: Wallet ID
            amount: Amount to add/subtract
            transaction_type: Type of transaction

        Returns:
            Updated wallet
        """
        wallet_doc = await self.wallets.find_one({"id": wallet_id})
        if not wallet_doc:
            raise ValueError(f"Wallet {wallet_id} not found")

        wallet = Wallet(**wallet_doc)

        if transaction_type in ["deposit", "refund"]:
            wallet.balance += amount
        elif transaction_type in ["withdrawal", "usage_charge"]:
            if wallet.available_balance < amount:
                raise ValueError("Insufficient balance")
            wallet.balance -= amount

        wallet.updated_at = datetime.utcnow()
        wallet.last_transaction_at = datetime.utcnow()

        await self.wallets.update_one(
            {"id": wallet_id},
            {"$set": wallet.dict()}
        )

        logger.info(f"Updated wallet {wallet_id} balance to {wallet.balance}")
        return wallet

    # ============================================================================
    # PAYMENT METHODS
    # ============================================================================

    async def add_payment_method(
        self,
        user_id: str,
        provider: PaymentProvider,
        method_type: PaymentMethodType,
        display_name: str,
        provider_payment_method_id: Optional[str] = None,
        **kwargs
    ) -> PaymentMethod:
        """
        Add new payment method for user.

        Args:
            user_id: User ID
            provider: Payment provider
            method_type: Payment method type
            display_name: Display name
            provider_payment_method_id: Provider's payment method ID
            **kwargs: Additional method-specific fields

        Returns:
            Created payment method
        """
        payment_method = PaymentMethod(
            user_id=user_id,
            provider=provider,
            method_type=method_type,
            display_name=display_name,
            provider_payment_method_id=provider_payment_method_id,
            **kwargs
        )

        # If this is first payment method, make it default
        existing_methods = await self.payment_methods.count_documents({"user_id": user_id})
        if existing_methods == 0:
            payment_method.is_default = True

        await self.payment_methods.insert_one(payment_method.dict())
        logger.info(f"Added payment method {payment_method.id} for user {user_id}")

        return payment_method

    async def get_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """
        Get all payment methods for user.

        Args:
            user_id: User ID

        Returns:
            List of payment methods
        """
        methods = []
        cursor = self.payment_methods.find({"user_id": user_id, "is_active": True})

        async for method_doc in cursor:
            methods.append(PaymentMethod(**method_doc))

        return methods

    async def set_default_payment_method(self, user_id: str, payment_method_id: str) -> bool:
        """
        Set default payment method.

        Args:
            user_id: User ID
            payment_method_id: Payment method ID

        Returns:
            Success status
        """
        # Unset all existing defaults
        await self.payment_methods.update_many(
            {"user_id": user_id},
            {"$set": {"is_default": False}}
        )

        # Set new default
        result = await self.payment_methods.update_one(
            {"id": payment_method_id, "user_id": user_id},
            {"$set": {"is_default": True, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count > 0

    # ============================================================================
    # DEPOSITS
    # ============================================================================

    async def create_deposit(
        self,
        user_id: str,
        amount: Decimal,
        currency: Currency,
        payment_method_id: str,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Create deposit transaction.

        Args:
            user_id: User ID
            amount: Deposit amount
            currency: Currency
            payment_method_id: Payment method to use
            description: Optional description

        Returns:
            Created transaction
        """
        # Get wallet
        wallet = await self.get_or_create_wallet(user_id, currency)

        # Get payment method
        method_doc = await self.payment_methods.find_one({"id": payment_method_id})
        if not method_doc:
            raise ValueError(f"Payment method {payment_method_id} not found")

        payment_method = PaymentMethod(**method_doc)

        # Calculate fees
        processing_fee = await self._calculate_processing_fee(amount, payment_method.provider)
        total_amount = amount + processing_fee

        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            wallet_id=wallet.id,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency=currency,
            processing_fee=processing_fee,
            total_amount=total_amount,
            payment_method_id=payment_method_id,
            payment_provider=payment_method.provider,
            description=description or f"Wallet deposit via {payment_method.display_name}",
            balance_before=wallet.balance,
            balance_after=wallet.balance  # Will be updated on completion
        )

        await self.transactions.insert_one(transaction.dict())
        logger.info(f"Created deposit transaction {transaction.id} for ${amount}")

        # Process payment based on provider
        if payment_method.provider == PaymentProvider.STRIPE:
            await self._process_stripe_deposit(transaction, payment_method)
        elif payment_method.provider == PaymentProvider.FLUTTERWAVE:
            await self._process_flutterwave_deposit(transaction, payment_method)
        elif payment_method.provider in [PaymentProvider.MTN_MOMO, PaymentProvider.VODAFONE_CASH, PaymentProvider.AIRTELTIGO_MONEY]:
            await self._process_mobile_money_deposit(transaction, payment_method)
        elif payment_method.provider == PaymentProvider.MPESA:
            await self._process_mpesa_deposit(transaction, payment_method)
        else:
            raise ValueError(f"Unsupported payment provider: {payment_method.provider}")

        return transaction

    async def _calculate_processing_fee(self, amount: Decimal, provider: PaymentProvider) -> Decimal:
        """
        Calculate processing fee for payment provider.

        Args:
            amount: Transaction amount
            provider: Payment provider

        Returns:
            Processing fee
        """
        # Fee structures (these should be configurable per provider)
        fee_configs = {
            PaymentProvider.STRIPE: {"percent": Decimal("2.9"), "fixed": Decimal("0.30")},
            PaymentProvider.FLUTTERWAVE: {"percent": Decimal("1.4"), "fixed": Decimal("0.00")},
            PaymentProvider.MTN_MOMO: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.VODAFONE_CASH: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.AIRTELTIGO_MONEY: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.MPESA: {"percent": Decimal("1.0"), "fixed": Decimal("0.00")},
        }

        config = fee_configs.get(provider, {"percent": Decimal("0.0"), "fixed": Decimal("0.0")})
        return (amount * config["percent"] / Decimal("100")) + config["fixed"]

    # ============================================================================
    # STRIPE INTEGRATION
    # ============================================================================

    async def _process_stripe_deposit(self, transaction: Transaction, payment_method: PaymentMethod):
        """
        Process deposit via Stripe using real Stripe client.

        Args:
            transaction: Transaction to process
            payment_method: Payment method
        """
        try:
            # Get Stripe config
            config = await self._get_provider_config(PaymentProvider.STRIPE)

            # Initialize Stripe client
            stripe_client = StripeClient(
                secret_key=config.secret_key,
                webhook_secret=config.webhook_secret
            )

            # Create Payment Intent
            result = await stripe_client.create_payment_intent(
                amount=transaction.total_amount,
                currency=transaction.currency.value,
                customer_id=payment_method.provider_customer_id,
                payment_method_id=payment_method.provider_payment_method_id,
                confirm=True,
                metadata={
                    "transaction_id": transaction.id,
                    "user_id": transaction.user_id,
                    "wallet_id": transaction.wallet_id
                }
            )

            # Update transaction
            transaction.provider_transaction_id = result["id"]
            transaction.provider_response = result
            transaction.status = TransactionStatus.PROCESSING
            transaction.updated_at = datetime.utcnow()

            await self.transactions.update_one(
                {"id": transaction.id},
                {"$set": transaction.dict()}
            )

            logger.info(f"Stripe payment intent created: {result['id']}")

        except ValueError as e:
            # Card declined or invalid request
            logger.error(f"Stripe deposit failed: {str(e)}")
            await self._fail_transaction(transaction.id, str(e))
            raise

        except Exception as e:
            logger.error(f"Stripe deposit error: {str(e)}")
            await self._fail_transaction(transaction.id, str(e))
            raise

    # ============================================================================
    # FLUTTERWAVE INTEGRATION
    # ============================================================================

    async def _process_flutterwave_deposit(self, transaction: Transaction, payment_method: PaymentMethod):
        """
        Process deposit via Flutterwave.

        Args:
            transaction: Transaction to process
            payment_method: Payment method
        """
        try:
            # Get Flutterwave config
            config = await self._get_provider_config(PaymentProvider.FLUTTERWAVE)

            # Create Flutterwave charge
            flw_data = {
                "tx_ref": transaction.id,
                "amount": str(transaction.total_amount),
                "currency": transaction.currency.value,
                "payment_type": "card" if payment_method.method_type == PaymentMethodType.CARD else "mobilemoney",
                "redirect_url": f"{config.webhook_url}/callback",
                "customer": {
                    "email": transaction.metadata.get("email", f"{transaction.user_id}@example.com"),
                    "name": transaction.metadata.get("name", "Customer")
                },
                "customizations": {
                    "title": "Wallet Deposit",
                    "description": transaction.description
                },
                "meta": {
                    "transaction_id": transaction.id,
                    "user_id": transaction.user_id
                }
            }

            response = await self.http_client.post(
                f"https://api.flutterwave.com/v3/payments",
                headers={
                    "Authorization": f"Bearer {config.secret_key}",
                    "Content-Type": "application/json"
                },
                json=flw_data
            )

            result = response.json()

            if result.get("status") == "success":
                # Update transaction
                transaction.provider_transaction_id = result["data"]["id"]
                transaction.provider_response = result
                transaction.status = TransactionStatus.PROCESSING
                transaction.updated_at = datetime.utcnow()

                await self.transactions.update_one(
                    {"id": transaction.id},
                    {"$set": transaction.dict()}
                )

                logger.info(f"Flutterwave charge created: {result['data']['id']}")
            else:
                raise Exception(f"Flutterwave error: {result.get('message')}")

        except Exception as e:
            logger.error(f"Flutterwave deposit failed: {str(e)}")
            await self._fail_transaction(transaction.id, str(e))
            raise

    # ============================================================================
    # MOBILE MONEY INTEGRATION (Ghana)
    # ============================================================================

    async def _process_mobile_money_deposit(self, transaction: Transaction, payment_method: PaymentMethod):
        """
        Process deposit via Mobile Money (MTN, Vodafone, AirtelTigo).

        Args:
            transaction: Transaction to process
            payment_method: Payment method
        """
        try:
            # Get Mobile Money config
            config = await self._get_provider_config(payment_method.provider)

            # Create mobile money charge
            momo_data = {
                "amount": str(transaction.total_amount),
                "currency": transaction.currency.value,
                "phone_number": payment_method.phone_number,
                "network": payment_method.provider.value,
                "reference": transaction.id,
                "description": transaction.description,
                "callback_url": f"{config.webhook_url}/momo-callback"
            }

            # Use Flutterwave for mobile money or direct provider API
            if config.settings.get("use_flutterwave"):
                response = await self._process_flutterwave_mobile_money(transaction, momo_data, config)
            else:
                response = await self._process_direct_mobile_money(transaction, momo_data, config)

            logger.info(f"Mobile money charge initiated for {payment_method.phone_number}")

        except Exception as e:
            logger.error(f"Mobile money deposit failed: {str(e)}")
            await self._fail_transaction(transaction.id, str(e))
            raise

    async def _process_flutterwave_mobile_money(
        self,
        transaction: Transaction,
        momo_data: Dict[str, Any],
        config: ProviderConfig
    ):
        """Process mobile money via Flutterwave."""
        response = await self.http_client.post(
            "https://api.flutterwave.com/v3/charges?type=mobile_money_ghana",
            headers={
                "Authorization": f"Bearer {config.secret_key}",
                "Content-Type": "application/json"
            },
            json={
                "tx_ref": transaction.id,
                "amount": momo_data["amount"],
                "currency": momo_data["currency"],
                "network": momo_data["network"].upper(),
                "phone_number": momo_data["phone_number"],
                "email": transaction.metadata.get("email", f"{transaction.user_id}@example.com")
            }
        )

        result = response.json()

        if result.get("status") == "success":
            transaction.provider_transaction_id = result["data"]["id"]
            transaction.provider_response = result
            transaction.status = TransactionStatus.PROCESSING
            transaction.updated_at = datetime.utcnow()

            await self.transactions.update_one(
                {"id": transaction.id},
                {"$set": transaction.dict()}
            )
        else:
            raise Exception(f"Flutterwave mobile money error: {result.get('message')}")

    # ============================================================================
    # M-PESA INTEGRATION (Kenya)
    # ============================================================================

    async def _process_mpesa_deposit(self, transaction: Transaction, payment_method: PaymentMethod):
        """
        Process deposit via M-Pesa (Kenya).

        Args:
            transaction: Transaction to process
            payment_method: Payment method
        """
        try:
            # Get M-Pesa config
            config = await self._get_provider_config(PaymentProvider.MPESA)

            # Get M-Pesa access token
            access_token = await self._get_mpesa_access_token(config)

            # Create STK Push request
            mpesa_data = {
                "BusinessShortCode": config.settings["short_code"],
                "Password": config.settings["password"],
                "Timestamp": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(transaction.total_amount),
                "PartyA": payment_method.phone_number,
                "PartyB": config.settings["short_code"],
                "PhoneNumber": payment_method.phone_number,
                "CallBackURL": f"{config.webhook_url}/mpesa-callback",
                "AccountReference": transaction.id,
                "TransactionDesc": transaction.description
            }

            response = await self.http_client.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=mpesa_data
            )

            result = response.json()

            if result.get("ResponseCode") == "0":
                transaction.provider_transaction_id = result["CheckoutRequestID"]
                transaction.provider_response = result
                transaction.status = TransactionStatus.PROCESSING
                transaction.updated_at = datetime.utcnow()

                await self.transactions.update_one(
                    {"id": transaction.id},
                    {"$set": transaction.dict()}
                )

                logger.info(f"M-Pesa STK push initiated: {result['CheckoutRequestID']}")
            else:
                raise Exception(f"M-Pesa error: {result.get('ResponseDescription')}")

        except Exception as e:
            logger.error(f"M-Pesa deposit failed: {str(e)}")
            await self._fail_transaction(transaction.id, str(e))
            raise

    async def _get_mpesa_access_token(self, config: ProviderConfig) -> str:
        """Get M-Pesa OAuth access token."""
        import base64

        credentials = f"{config.api_key}:{config.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = await self.http_client.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {encoded}"}
        )

        result = response.json()
        return result["access_token"]

    # ============================================================================
    # WEBHOOK HANDLERS
    # ============================================================================

    async def handle_webhook(
        self,
        provider: PaymentProvider,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle payment webhook from provider.

        Args:
            provider: Payment provider
            payload: Webhook payload
            signature: Webhook signature
            headers: Request headers

        Returns:
            Processing result
        """
        # Create webhook event record
        event = WebhookEvent(
            provider=provider,
            event_type=payload.get("type") or payload.get("event"),
            event_id=payload.get("id"),
            raw_payload=payload,
            headers=headers or {},
            verification_signature=signature
        )

        try:
            # Verify webhook signature
            is_verified = await self._verify_webhook_signature(provider, payload, signature)
            event.is_verified = is_verified

            if not is_verified:
                logger.warning(f"Invalid webhook signature from {provider.value}")
                event.processing_error = "Invalid signature"
                await self.webhook_events.insert_one(event.dict())
                return {"success": False, "error": "Invalid signature"}

            # Process webhook based on provider
            if provider == PaymentProvider.STRIPE:
                result = await self._process_stripe_webhook(payload)
            elif provider == PaymentProvider.FLUTTERWAVE:
                result = await self._process_flutterwave_webhook(payload)
            elif provider in [PaymentProvider.MTN_MOMO, PaymentProvider.VODAFONE_CASH, PaymentProvider.AIRTELTIGO_MONEY]:
                result = await self._process_mobile_money_webhook(payload)
            elif provider == PaymentProvider.MPESA:
                result = await self._process_mpesa_webhook(payload)
            else:
                raise ValueError(f"Unsupported provider: {provider.value}")

            event.is_processed = True
            event.processed_at = datetime.utcnow()
            event.transaction_id = result.get("transaction_id")

            await self.webhook_events.insert_one(event.dict())
            logger.info(f"Processed {provider.value} webhook: {event.event_type}")

            return {"success": True, "transaction_id": result.get("transaction_id")}

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            event.processing_error = str(e)
            event.processing_attempts += 1
            await self.webhook_events.insert_one(event.dict())
            return {"success": False, "error": str(e)}

    async def _process_stripe_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe webhook."""
        event_type = payload["type"]

        if event_type == "payment_intent.succeeded":
            payment_intent = payload["data"]["object"]
            transaction_id = payment_intent["metadata"]["transaction_id"]
            await self._complete_transaction(transaction_id, payload)
            return {"transaction_id": transaction_id}

        elif event_type == "payment_intent.payment_failed":
            payment_intent = payload["data"]["object"]
            transaction_id = payment_intent["metadata"]["transaction_id"]
            failure_message = payment_intent.get("last_payment_error", {}).get("message")
            await self._fail_transaction(transaction_id, failure_message)
            return {"transaction_id": transaction_id}

        return {}

    async def _process_flutterwave_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Flutterwave webhook."""
        if payload.get("status") == "successful":
            transaction_id = payload["data"]["tx_ref"]
            await self._complete_transaction(transaction_id, payload)
            return {"transaction_id": transaction_id}

        elif payload.get("status") == "failed":
            transaction_id = payload["data"]["tx_ref"]
            await self._fail_transaction(transaction_id, "Payment failed")
            return {"transaction_id": transaction_id}

        return {}

    async def _process_mobile_money_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Mobile Money webhook."""
        # Mobile money webhooks typically come through Flutterwave
        return await self._process_flutterwave_webhook(payload)

    async def _process_mpesa_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process M-Pesa webhook."""
        callback_data = payload.get("Body", {}).get("stkCallback", {})
        result_code = callback_data.get("ResultCode")

        transaction_id = callback_data.get("MerchantRequestID")

        if result_code == 0:
            await self._complete_transaction(transaction_id, payload)
        else:
            result_desc = callback_data.get("ResultDesc")
            await self._fail_transaction(transaction_id, result_desc)

        return {"transaction_id": transaction_id}

    async def _verify_webhook_signature(
        self,
        provider: PaymentProvider,
        payload: Dict[str, Any],
        signature: Optional[str],
        raw_payload: Optional[str] = None
    ) -> bool:
        """
        Verify webhook signature using real provider verification.

        Args:
            provider: Payment provider
            payload: Webhook payload (dict)
            signature: Signature to verify
            raw_payload: Raw request body string (for Stripe)

        Returns:
            True if signature is valid
        """
        if not signature:
            logger.warning("No signature provided for webhook verification")
            return False

        try:
            config = await self._get_provider_config(provider)

            if provider == PaymentProvider.STRIPE:
                # Real Stripe signature verification
                if not raw_payload:
                    logger.error("Raw payload required for Stripe webhook verification")
                    return False

                stripe_client = StripeClient(
                    secret_key=config.secret_key,
                    webhook_secret=config.webhook_secret
                )

                try:
                    # This will raise ValueError if signature is invalid
                    stripe_client.verify_webhook_signature(raw_payload, signature)
                    return True
                except ValueError:
                    return False

            elif provider == PaymentProvider.FLUTTERWAVE:
                # Flutterwave uses secret hash
                expected_hash = hashlib.sha256(
                    config.webhook_secret.encode()
                ).hexdigest()
                return signature == expected_hash

            else:
                # For other providers, implement specific verification
                logger.warning(f"Webhook verification not implemented for {provider.value}")
                return True  # Allow for now, but should implement

        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    # ============================================================================
    # TRANSACTION MANAGEMENT
    # ============================================================================

    async def _complete_transaction(self, transaction_id: str, provider_response: Dict[str, Any]):
        """
        Complete a successful transaction.

        Args:
            transaction_id: Transaction ID
            provider_response: Provider response data
        """
        transaction_doc = await self.transactions.find_one({"id": transaction_id})
        if not transaction_doc:
            logger.error(f"Transaction {transaction_id} not found")
            return

        transaction = Transaction(**transaction_doc)

        # Update wallet balance
        wallet = await self.update_wallet_balance(
            transaction.wallet_id,
            transaction.amount,
            transaction.transaction_type.value
        )

        # Update transaction
        transaction.status = TransactionStatus.COMPLETED
        transaction.balance_after = wallet.balance
        transaction.completed_at = datetime.utcnow()
        transaction.updated_at = datetime.utcnow()
        transaction.provider_response.update(provider_response)

        await self.transactions.update_one(
            {"id": transaction_id},
            {"$set": transaction.dict()}
        )

        logger.info(f"Completed transaction {transaction_id}")

        # Send email notification for successful deposit
        if transaction.transaction_type == TransactionType.DEPOSIT:
            try:
                # Get user email from user_id
                # For now, we'll need to fetch from MongoDB users collection
                user_doc = await self.db.users.find_one({"id": transaction.user_id})
                if user_doc and user_doc.get("email"):
                    user_email = user_doc["email"]

                    # Get payment method display name
                    payment_method_display = "Unknown"
                    if transaction.payment_method_id:
                        payment_method_doc = await self.payment_methods.find_one({"id": transaction.payment_method_id})
                        if payment_method_doc:
                            payment_method_display = payment_method_doc.get("display_name", "Unknown")

                    # Send email notification
                    asyncio.create_task(
                        wallet_notification_service.send_deposit_success_email(
                            to_email=user_email,
                            amount=transaction.amount,
                            currency=transaction.currency.value,
                            transaction_id=transaction.id,
                            payment_method=payment_method_display,
                            processing_fee=transaction.processing_fee,
                            new_balance=wallet.balance,
                            transaction_date=transaction.completed_at.strftime("%B %d, %Y at %I:%M %p UTC")
                        )
                    )
                    logger.info(f"Queued deposit success email for user {transaction.user_id}")

                    # Send SMS for mobile money transactions
                    if transaction.payment_provider in [
                        PaymentProvider.MTN_MOMO,
                        PaymentProvider.VODAFONE_CASH,
                        PaymentProvider.AIRTELTIGO_MONEY,
                        PaymentProvider.MPESA
                    ]:
                        # Get phone number from payment method
                        if transaction.payment_method_id:
                            payment_method_doc = await self.payment_methods.find_one({"id": transaction.payment_method_id})
                            if payment_method_doc and payment_method_doc.get("phone_number"):
                                phone_number = payment_method_doc["phone_number"]

                                # Send SMS notification
                                asyncio.create_task(
                                    wallet_notification_service.send_deposit_success_sms(
                                        to_number=phone_number,
                                        amount=transaction.amount,
                                        currency=transaction.currency.value,
                                        new_balance=wallet.balance
                                    )
                                )
                                logger.info(f"Queued deposit success SMS for {phone_number}")

            except Exception as e:
                # Don't fail transaction if notification fails
                logger.error(f"Failed to send deposit notifications: {e}")

    async def _fail_transaction(self, transaction_id: str, failure_reason: str):
        """
        Mark transaction as failed.

        Args:
            transaction_id: Transaction ID
            failure_reason: Reason for failure
        """
        await self.transactions.update_one(
            {"id": transaction_id},
            {
                "$set": {
                    "status": TransactionStatus.FAILED.value,
                    "failure_reason": failure_reason,
                    "failed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Failed transaction {transaction_id}: {failure_reason}")

    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        transaction_doc = await self.transactions.find_one({"id": transaction_id})
        if transaction_doc:
            return Transaction(**transaction_doc)
        return None

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transaction history for user.

        Args:
            user_id: User ID
            limit: Number of transactions
            offset: Offset for pagination

        Returns:
            List of transactions
        """
        transactions = []
        cursor = self.transactions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(offset).limit(limit)

        async for tx_doc in cursor:
            transactions.append(Transaction(**tx_doc))

        return transactions

    # ============================================================================
    # PROVIDER CONFIGURATION
    # ============================================================================

    async def _get_provider_config(self, provider: PaymentProvider) -> ProviderConfig:
        """
        Get provider configuration.

        Args:
            provider: Payment provider

        Returns:
            Provider config
        """
        config_doc = await self.provider_configs.find_one({
            "provider": provider.value,
            "is_active": True
        })

        if not config_doc:
            raise ValueError(f"No configuration found for {provider.value}")

        return ProviderConfig(**config_doc)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
