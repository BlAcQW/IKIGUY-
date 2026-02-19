"""
TTS Billing Manager

Handles automatic wallet deduction for TTS synthesis operations.
Integrates with WalletService and UsageCalculator for accurate cost tracking.

Usage:
    from apps.shared.tts.billing import TTSBillingManager
    from apps.shared.integration.wallet import WalletService

    wallet_service = WalletService(database=db)
    billing_manager = TTSBillingManager(wallet_service=wallet_service)

    # Synthesize with automatic billing
    response, transaction = await billing_manager.synthesize_with_billing(
        user_id="user123",
        text="Hello world",
        provider=TTSProvider.COQUI_XTTS,
        language="en"
    )

Author: KasaAI Team
Date: 2025-11-23
"""

from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
import logging
import hashlib

from .client import AsyncTTSClient
from .models import (
    TTSProvider,
    TTSRequest,
    TTSResponse,
    VoiceCloneRequest,
    AudioFormat,
)
from .exceptions import TTSException, InvalidRequestError

from shared.integration.wallet import (
    WalletService,
    Currency,
    Transaction,
    Wallet,
)
from shared.integration.wallet.exceptions import (
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletSuspendedError,
    WalletClosedError,
    DuplicateTransactionError,
)
from shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier,
    ServiceType,
    UsageMetric,
)

logger = logging.getLogger(__name__)


class TTSBillingManager:
    """
    Manages billing for TTS synthesis operations.

    Automatically deducts costs from user wallets before synthesis
    and provides refunds on failure.
    """

    def __init__(
        self,
        wallet_service: WalletService,
        pricing_tier: PricingTier = PricingTier.BASIC,
        currency: Currency = Currency.GHS,
        enable_refunds: bool = True,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize TTSBillingManager.

        Args:
            wallet_service: WalletService instance for transactions
            pricing_tier: Pricing tier for cost calculation
            currency: Currency for transactions
            enable_refunds: Whether to refund on synthesis failure
            tenant_id: Optional tenant ID for multi-tenancy
        """
        self.wallet_service = wallet_service
        self.pricing_tier = pricing_tier
        self.currency = currency
        self.enable_refunds = enable_refunds
        self.tenant_id = tenant_id

        # Initialize usage calculator
        self.usage_calculator = UsageCalculator(
            tier=pricing_tier,
            tenant_id=tenant_id,
            enable_cost_tracking=True
        )

        logger.info(
            f"TTSBillingManager initialized: "
            f"tier={pricing_tier.value}, currency={currency.value}"
        )

    async def estimate_cost(
        self,
        text: str,
        provider: TTSProvider,
        voice_cloning: bool = False
    ) -> Decimal:
        """
        Estimate cost for TTS synthesis.

        Args:
            text: Text to synthesize
            provider: TTS provider to use
            voice_cloning: Whether voice cloning is enabled

        Returns:
            Estimated cost in configured currency
        """
        # Calculate base cost
        num_characters = len(text)
        cost_metric = self.usage_calculator.calculate_tts_cost(
            num_characters=num_characters,
            provider=provider.value,
            voice="default"
        )

        base_cost = cost_metric.total_cost

        # Apply voice cloning multiplier (2x for cloning)
        if voice_cloning:
            base_cost = base_cost * Decimal("2.0")

        logger.debug(
            f"Cost estimate: {base_cost} {self.currency.value} "
            f"({num_characters} chars, provider={provider.value}, "
            f"voice_cloning={voice_cloning})"
        )

        return base_cost

    async def check_balance(
        self,
        user_id: str,
        required_amount: Decimal
    ) -> bool:
        """
        Check if user has sufficient balance.

        Args:
            user_id: User ID
            required_amount: Amount required for operation

        Returns:
            True if sufficient balance, False otherwise
        """
        try:
            wallet = await self.wallet_service.get_wallet_by_user(
                user_id=user_id,
                currency=self.currency
            )

            if not wallet:
                logger.warning(f"No wallet found for user {user_id}")
                return False

            has_balance = wallet.balance >= required_amount

            logger.debug(
                f"Balance check for {user_id}: "
                f"required={required_amount}, available={wallet.balance}, "
                f"sufficient={has_balance}"
            )

            return has_balance

        except Exception as e:
            logger.error(f"Balance check error: {str(e)}")
            return False

    async def synthesize_with_billing(
        self,
        user_id: str,
        text: str,
        provider: Optional[TTSProvider] = None,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0,
        output_format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 22050,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[TTSResponse, Optional[Transaction]]:
        """
        Synthesize speech with automatic billing.

        Args:
            user_id: User ID for billing
            text: Text to synthesize
            provider: TTS provider (auto-selects if None)
            language: Language code
            speaker: Speaker/voice ID
            speed: Speech speed (0.5-2.0)
            output_format: Audio output format
            sample_rate: Audio sample rate
            metadata: Additional metadata for transaction
            **kwargs: Additional TTS parameters

        Returns:
            Tuple of (TTSResponse, Optional[Transaction]) - Transaction is None for zero-cost requests

        Raises:
            WalletNotFoundError: No wallet exists for user
            InsufficientBalanceError: Insufficient wallet balance
            WalletSuspendedError: Wallet is suspended
            WalletClosedError: Wallet is closed
            TTSException: TTS synthesis failed
        """
        # Generate request ID for idempotency
        request_id = self._generate_request_id(
            user_id, text, provider, language, speaker
        )

        # Estimate cost
        provider_enum = provider or TTSProvider.COQUI_XTTS
        estimated_cost = await self.estimate_cost(
            text=text,
            provider=provider_enum,
            voice_cloning=False
        )

        # Get user wallet, auto-create if doesn't exist
        wallet = await self.wallet_service.get_wallet_by_user(
            user_id=user_id,
            currency=self.currency
        )

        if not wallet:
            # Auto-create wallet for new users with zero balance
            logger.info(f"Auto-creating wallet for user {user_id}")
            try:
                wallet = await self.wallet_service.create_wallet(
                    user_id=user_id,
                    currency=self.currency,
                    tenant_id=self.tenant_id
                )
            except Exception as e:
                logger.error(f"Failed to auto-create wallet for {user_id}: {e}")
                raise WalletNotFoundError(f"No wallet found for user {user_id} and auto-creation failed: {e}")

        # Check balance (only if cost > 0)
        if estimated_cost > 0 and wallet.balance < estimated_cost:
            raise InsufficientBalanceError(
                f"Insufficient balance. Required: {estimated_cost} {self.currency.value}, "
                f"Available: {wallet.balance} {self.currency.value}"
            )

        # Prepare transaction metadata
        transaction_metadata = {
            "service": "tts",
            "provider_id": provider_enum.value,
            "provider_name": provider_enum.value.replace("_", " ").title(),
            "character_count": len(text),
            "voice_id": speaker or "default",
            "language": language,
            "audio_format": output_format.value,
            "voice_cloning": False,
            "request_id": request_id,
            **(metadata or {})
        }

        # Debit wallet (skip if cost is 0 - e.g., free tier)
        transaction = None
        if estimated_cost > 0:
            try:
                transaction = await self.wallet_service.debit(
                    wallet_id=wallet.id,
                    amount=estimated_cost,
                    description=f"TTS Synthesis: {provider_enum.value} - {len(text)} characters",
                    idempotency_key=f"tts:{user_id}:{request_id}",
                    metadata=transaction_metadata
                )

                logger.info(
                    f"Wallet debited: {estimated_cost} {self.currency.value} "
                    f"for user {user_id} (transaction: {transaction.id})"
                )

            except DuplicateTransactionError as e:
                logger.warning(f"Duplicate transaction detected: {str(e)}")
                # Transaction already exists, retrieve it
                # For now, re-raise to avoid synthesis
                raise
        else:
            logger.info(
                f"Skipping wallet debit for zero-cost TTS synthesis "
                f"(user: {user_id}, provider: {provider_enum.value})"
            )

        # Synthesize audio
        start_time = datetime.utcnow()
        response = None

        try:
            async with AsyncTTSClient() as client:
                response = await client.synthesize(
                    text=text,
                    provider=provider,
                    language=language,
                    speaker=speaker,
                    speed=speed,
                    output_format=output_format,
                    sample_rate=sample_rate,
                    **kwargs
                )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Update transaction metadata with actual results
            transaction_metadata.update({
                "duration_seconds": response.duration,
                "processing_time": processing_time,
                "actual_cost": float(estimated_cost),
                "status": "completed"
            })

            logger.info(
                f"TTS synthesis completed: {len(text)} chars, "
                f"duration={response.duration}s, processing={processing_time}s"
            )

            return response, transaction

        except Exception as e:
            logger.error(f"TTS synthesis failed: {str(e)}")

            # Refund on failure
            if self.enable_refunds and transaction:
                try:
                    await self.wallet_service.refund(
                        transaction_id=str(transaction.id),
                        reason=f"TTS synthesis failed: {str(e)}"
                    )
                    logger.info(f"Refunded transaction {transaction.id}")
                except Exception as refund_error:
                    logger.error(f"Refund failed: {str(refund_error)}")

            # Re-raise original exception
            raise TTSException(f"Synthesis failed: {str(e)}") from e

    async def clone_voice_with_billing(
        self,
        user_id: str,
        text: str,
        reference_audio: bytes,
        provider: Optional[TTSProvider] = None,
        language: str = "en",
        speed: float = 1.0,
        output_format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 22050,
        enhance: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[TTSResponse, Optional[Transaction]]:
        """
        Clone voice with automatic billing.

        Note: Voice cloning costs 2x standard synthesis.

        Args:
            user_id: User ID for billing
            text: Text to synthesize
            reference_audio: Reference audio for cloning
            provider: TTS provider (auto-selects if None)
            language: Language code
            speed: Speech speed (0.5-2.0)
            output_format: Audio output format
            sample_rate: Audio sample rate
            enhance: Apply audio enhancement
            metadata: Additional metadata for transaction
            **kwargs: Additional TTS parameters

        Returns:
            Tuple of (TTSResponse, Optional[Transaction]) - Transaction is None for zero-cost requests

        Raises:
            WalletNotFoundError: No wallet exists for user
            InsufficientBalanceError: Insufficient wallet balance
            TTSException: Voice cloning failed
        """
        # Generate request ID for idempotency
        request_id = self._generate_request_id(
            user_id, text, provider, language, speaker=None, voice_cloning=True
        )

        # Estimate cost (2x for voice cloning)
        provider_enum = provider or TTSProvider.COQUI_XTTS
        estimated_cost = await self.estimate_cost(
            text=text,
            provider=provider_enum,
            voice_cloning=True
        )

        # Get user wallet, auto-create if doesn't exist
        wallet = await self.wallet_service.get_wallet_by_user(
            user_id=user_id,
            currency=self.currency
        )

        if not wallet:
            # Auto-create wallet for new users with zero balance
            logger.info(f"Auto-creating wallet for user {user_id} (voice clone)")
            try:
                wallet = await self.wallet_service.create_wallet(
                    user_id=user_id,
                    currency=self.currency,
                    tenant_id=self.tenant_id
                )
            except Exception as e:
                logger.error(f"Failed to auto-create wallet for {user_id}: {e}")
                raise WalletNotFoundError(f"No wallet found for user {user_id} and auto-creation failed: {e}")

        # Check balance (only if cost > 0)
        if estimated_cost > 0 and wallet.balance < estimated_cost:
            raise InsufficientBalanceError(
                f"Insufficient balance. Required: {estimated_cost} {self.currency.value}, "
                f"Available: {wallet.balance} {self.currency.value}"
            )

        # Prepare transaction metadata
        transaction_metadata = {
            "service": "tts",
            "provider_id": provider_enum.value,
            "provider_name": provider_enum.value.replace("_", " ").title(),
            "character_count": len(text),
            "voice_id": "cloned",
            "language": language,
            "audio_format": output_format.value,
            "voice_cloning": True,
            "reference_audio_size": len(reference_audio),
            "request_id": request_id,
            **(metadata or {})
        }

        # Debit wallet (skip if cost is 0 - e.g., free tier)
        transaction = None
        if estimated_cost > 0:
            try:
                transaction = await self.wallet_service.debit(
                    wallet_id=wallet.id,
                    amount=estimated_cost,
                    description=f"TTS Voice Cloning: {provider_enum.value} - {len(text)} characters",
                    idempotency_key=f"tts_clone:{user_id}:{request_id}",
                    metadata=transaction_metadata
                )

                logger.info(
                    f"Wallet debited for voice cloning: {estimated_cost} {self.currency.value} "
                    f"for user {user_id} (transaction: {transaction.id})"
                )

            except DuplicateTransactionError as e:
                logger.warning(f"Duplicate transaction detected: {str(e)}")
                raise
        else:
            logger.info(
                f"Skipping wallet debit for zero-cost voice cloning "
                f"(user: {user_id}, provider: {provider_enum.value})"
            )

        # Clone voice
        start_time = datetime.utcnow()
        response = None

        try:
            async with AsyncTTSClient() as client:
                response = await client.clone_voice(
                    text=text,
                    reference_audio=reference_audio,
                    provider=provider,
                    language=language,
                    speed=speed,
                    output_format=output_format,
                    sample_rate=sample_rate,
                    enhance=enhance,
                    **kwargs
                )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Update transaction metadata
            transaction_metadata.update({
                "duration_seconds": response.duration,
                "processing_time": processing_time,
                "actual_cost": float(estimated_cost),
                "status": "completed"
            })

            logger.info(
                f"Voice cloning completed: {len(text)} chars, "
                f"duration={response.duration}s, processing={processing_time}s"
            )

            return response, transaction

        except Exception as e:
            logger.error(f"Voice cloning failed: {str(e)}")

            # Refund on failure
            if self.enable_refunds and transaction:
                try:
                    await self.wallet_service.refund(
                        transaction_id=str(transaction.id),
                        reason=f"Voice cloning failed: {str(e)}"
                    )
                    logger.info(f"Refunded transaction {transaction.id}")
                except Exception as refund_error:
                    logger.error(f"Refund failed: {str(refund_error)}")

            # Re-raise original exception
            raise TTSException(f"Voice cloning failed: {str(e)}") from e

    def _generate_request_id(
        self,
        user_id: str,
        text: str,
        provider: Optional[TTSProvider],
        language: str,
        speaker: Optional[str] = None,
        voice_cloning: bool = False
    ) -> str:
        """
        Generate unique request ID for idempotency.

        Args:
            user_id: User ID
            text: Text to synthesize
            provider: TTS provider
            language: Language code
            speaker: Speaker/voice ID
            voice_cloning: Whether voice cloning is enabled

        Returns:
            SHA256 hash of request parameters
        """
        # Create unique string from request parameters
        provider_str = provider.value if provider else "auto"
        speaker_str = speaker or "default"
        clone_str = "clone" if voice_cloning else "synth"

        request_string = f"{user_id}:{text}:{provider_str}:{language}:{speaker_str}:{clone_str}"

        # Generate SHA256 hash
        request_hash = hashlib.sha256(request_string.encode()).hexdigest()[:16]

        return request_hash
