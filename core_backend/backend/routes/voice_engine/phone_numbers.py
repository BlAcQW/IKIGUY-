"""
Phone Number Management for Kasaai Voice Engine
Handles phone number provisioning, porting, and management from multiple providers
"""

import logging
import json
import os
import sys
import random
import secrets
import string
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import aiohttp
from enum import Enum
from pymongo import MongoClient
from bson import ObjectId

# Import SMTP for fallback email sending
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Import low credit notifier from shared services
try:
    from apps.shared.services.low_credit_notifier import get_low_credit_notifier
    LOW_CREDIT_NOTIFIER_AVAILABLE = True
    logger.info("LowCreditNotifier available for low credit alerts")
except ImportError:
    LOW_CREDIT_NOTIFIER_AVAILABLE = False
    logger.warning("LowCreditNotifier not available, using fallback SMTP")

# Import FreeSWITCH API client
FREESWITCH_API_AVAILABLE = False
try:
    from apps.shared.freeswitch_api.client import FreeSWITCHAPIClient
    FREESWITCH_API_AVAILABLE = True
    logger.info("FreeSWITCH API client imported successfully")
except ImportError as e:
    logger.warning(f"FreeSWITCH API client not available: {e}")
    # Create a dummy class for type hints
    class FreeSWITCHAPIClient:
        pass

# Import Asterisk API client (deprecated - keeping for backward compatibility)
ASTERISK_API_AVAILABLE = False
try:
    from apps.shared.asterisk_api.client import AsteriskAPIClient
    ASTERISK_API_AVAILABLE = True
    logger.info("Asterisk API client imported successfully (deprecated)")
except ImportError as e:
    logger.warning(f"Asterisk API client not available: {e}")
    # Create a dummy class for type hints
    class AsteriskAPIClient:
        pass

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])


class PhoneProvider(str, Enum):
    """Supported phone number providers"""
    KASAAI = "kasaai"
    TWILIO = "twilio"
    VONAGE = "vonage"
    TELNYX = "telnyx"
    VAPI = "vapi"
    SIP_TRUNK = "sip_trunk"
    ASTERISK = "asterisk"
    FREESWITCH = "freeswitch"


class PhoneNumberType(str, Enum):
    """Phone number types"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BOTH = "both"


class PhoneNumberStatus(str, Enum):
    """Phone number status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    PORTING = "porting"
    FAILED = "failed"


class PhoneNumber(BaseModel):
    """Phone number model"""
    id: str
    number: str
    provider: PhoneProvider
    type: PhoneNumberType
    status: PhoneNumberStatus
    country: str
    country_code: str
    capabilities: List[str] = Field(default_factory=list)
    monthly_cost: Optional[float] = None
    setup_cost: Optional[float] = None
    ported_from: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password: Optional[str] = None
    sip_server: Optional[str] = None
    webhook_url: Optional[str] = None

    # Assignment fields (one-to-one with Assistant)
    assigned_assistant_id: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Cost tracking and billing fields
    cost_per_minute: float = 0.15  # Default to GHC 0.15 for MTN
    credit_balance: float = 0.0  # Credit balance in local currency
    total_minutes_used: float = 0.0  # Total minutes used
    total_cost_spent: float = 0.0  # Total cost spent
    currency: str = "GHC"  # Currency code (GHC, USD, etc.)
    low_balance_threshold: float = 200.0  # Alert when balance drops below this (default 200 GHC)

    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionType(str, Enum):
    """Credit transaction types"""
    CREDIT = "credit"  # Adding credit
    DEBIT = "debit"  # Deducting credit (call usage)


class CreditTransaction(BaseModel):
    """Credit transaction model for audit trail"""
    id: str  # Transaction ID
    phone_id: str  # Phone number ID
    phone_number: str  # Phone number for easy reference
    amount: float  # Transaction amount (positive for credit, negative for debit)
    transaction_type: TransactionType
    timestamp: datetime
    balance_before: float  # Balance before transaction
    balance_after: float  # Balance after transaction

    # Audit fields
    added_by_user_id: Optional[str] = None  # User who added credit
    payment_method: Optional[str] = None  # cash, mobile_money, bank_transfer, etc.
    reference_number: Optional[str] = None  # Payment reference
    notes: Optional[str] = None  # Additional notes

    # Call-related fields (for debit transactions)
    call_id: Optional[str] = None  # Associated call ID
    call_duration_seconds: Optional[int] = None  # Call duration
    call_duration_minutes: Optional[float] = None  # Call duration in minutes
    campaign_id: Optional[str] = None  # Associated campaign ID

    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Provider configuration model"""
    provider: PhoneProvider
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    webhook_url: Optional[str] = None
    sip_server: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password: Optional[str] = None
    phone_id: Optional[str] = None  # For VAPI BYO phone import


class ImportRequest(BaseModel):
    """Request to import phone numbers from a provider"""
    provider: PhoneProvider
    config: ProviderConfig
    filter_country: Optional[str] = None
    filter_capabilities: Optional[List[str]] = None


class ProvisionRequest(BaseModel):
    """Request to provision a new phone number"""
    provider: PhoneProvider
    country_code: str
    area_code: Optional[str] = None
    capabilities: List[str] = Field(default_factory=lambda: ["voice", "sms"])
    plan: Optional[str] = "starter"
    sip_provider: Optional[str] = "freeswitch"  # "freeswitch" or "asterisk"


class PhoneNumberManager:
    """Manages phone numbers across different providers"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.phone_numbers: Dict[str, PhoneNumber] = {}
        self.provider_configs: Dict[PhoneProvider, ProviderConfig] = {}

        # Initialize MongoDB connection
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            self.mongo_client = MongoClient(mongodb_url)
            db_name = os.getenv("MONGODB_DB_NAME", "kasaai_core")
            self.db = self.mongo_client[db_name]
            # Use separate collection to avoid conflict with FreeSWITCH phone_numbers collection
            self.phone_numbers_collection = self.db["managed_phone_numbers"]
            # Credit transactions collection for audit trail
            self.credit_transactions_collection = self.db["phone_credit_transactions"]
            logger.info(f"MongoDB connected: {db_name}")

            # Load existing phone numbers from database
            self._load_from_database()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
            self.phone_numbers_collection = None
            self.credit_transactions_collection = None

        # Initialize FreeSWITCH API client (primary)
        if FREESWITCH_API_AVAILABLE:
            freeswitch_api_url = os.getenv("FREESWITCH_API_URL", "http://localhost:30041")
            self.freeswitch_client = FreeSWITCHAPIClient(base_url=freeswitch_api_url)
            logger.info(f"FreeSWITCH API client initialized: {freeswitch_api_url}")
        else:
            self.freeswitch_client = None
            logger.warning("FreeSWITCH API client not available")

        # Initialize Asterisk API client (deprecated - fallback)
        if ASTERISK_API_AVAILABLE:
            asterisk_api_url = os.getenv("ASTERISK_API_URL", "https://asterisk-api.ailabsafrica.com")
            self.asterisk_client = AsteriskAPIClient(base_url=asterisk_api_url)
            logger.info(f"Asterisk API client initialized (deprecated): {asterisk_api_url}")
        else:
            self.asterisk_client = None

        # Determine which client to use
        if self.freeswitch_client:
            logger.info("Using FreeSWITCH for SIP registration")
        elif self.asterisk_client:
            logger.warning("Using deprecated Asterisk client - consider migrating to FreeSWITCH")
        else:
            logger.warning("No SIP client available - provisioning will be simulated")

        # Email configuration for low balance alerts (using direct SMTP like call_management.py)
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@ailabsafrica.com")

    async def send_low_balance_alert(self, phone: PhoneNumber, balance_after_deduction: float):
        """
        Send email alert when phone number balance falls below threshold.
        Uses the shared LowCreditNotifier service for consistency with TTS health alerts.

        Args:
            phone: PhoneNumber object
            balance_after_deduction: Balance after deduction
        """
        try:
            # Check if balance crossed below threshold
            if balance_after_deduction < phone.low_balance_threshold:
                if LOW_CREDIT_NOTIFIER_AVAILABLE:
                    # Use the shared low credit notifier service
                    notifier = get_low_credit_notifier()
                    await notifier.send_low_credit_alert(
                        phone_number=phone.number,
                        phone_id=phone.id,
                        provider=phone.provider.value if hasattr(phone.provider, 'value') else str(phone.provider),
                        current_balance=balance_after_deduction,
                        threshold=phone.low_balance_threshold,
                        currency=phone.currency,
                        cost_per_minute=phone.cost_per_minute,
                        recipient_email="alfred.anyan@gmail.com"
                    )
                    logger.info(f"Low balance alert sent via notifier for {phone.number}: Balance {balance_after_deduction:.2f} {phone.currency}")
                else:
                    # Fallback to direct SMTP if notifier not available
                    await self._send_low_balance_alert_fallback(phone, balance_after_deduction)

        except Exception as e:
            logger.error(f"Failed to send low balance alert for {phone.number}: {e}")

    async def _send_low_balance_alert_fallback(self, phone: PhoneNumber, balance_after_deduction: float):
        """Fallback method for sending low balance alerts via direct SMTP."""
        try:
            remaining_minutes = balance_after_deduction / phone.cost_per_minute if phone.cost_per_minute > 0 else 0
            subject = f"🚨 Low Balance Alert: {phone.number}"

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #fee; border-left: 4px solid #dc2626; padding: 20px; margin-bottom: 20px;">
                    <h2 style="color: #dc2626; margin-top: 0;">⚠️ Low Balance Alert</h2>
                    <p style="font-size: 16px; color: #333;">
                        The VAPI phone number <strong>{phone.number}</strong> has fallen below the low balance threshold.
                    </p>
                </div>
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px;">
                    <p><strong>Current Balance:</strong> {phone.currency} {balance_after_deduction:.2f}</p>
                    <p><strong>Threshold:</strong> {phone.currency} {phone.low_balance_threshold:.2f}</p>
                    <p><strong>Remaining Minutes:</strong> {remaining_minutes:.1f}</p>
                </div>
                <p style="margin-top: 20px; color: #92400e;">
                    <strong>⚡ Action Required:</strong> Please add credit to avoid service interruption.
                </p>
            </body>
            </html>
            """

            plain_body = f"Low Balance Alert: {phone.number}\nBalance: {phone.currency} {balance_after_deduction:.2f}\nThreshold: {phone.currency} {phone.low_balance_threshold:.2f}"

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = "alfred.anyan@gmail.com"
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            if self.smtp_port == 587:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.sender_email, ["alfred.anyan@gmail.com"], msg.as_string())
            server.quit()

            logger.info(f"Low balance alert sent (fallback) for {phone.number}: Balance {balance_after_deduction:.2f} {phone.currency}")
        except Exception as email_error:
            logger.error(f"Failed to send low balance alert (fallback) for {phone.number}: {email_error}")

    async def initialize(self):
        """Initialize phone number manager"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    def _load_from_database(self):
        """Load phone numbers from MongoDB on startup"""
        if self.phone_numbers_collection is None:
            logger.warning("MongoDB not available - phone numbers will not persist")
            return

        try:
            count = 0
            for doc in self.phone_numbers_collection.find():
                # Convert MongoDB document to PhoneNumber model
                phone_data = {
                    "id": doc.get("id", str(doc.get("_id"))),
                    "number": doc["number"],
                    "provider": doc["provider"],
                    "type": doc["type"],
                    "status": doc["status"],
                    "country": doc["country"],
                    "country_code": doc["country_code"],
                    "capabilities": doc.get("capabilities", []),
                    "monthly_cost": doc.get("monthly_cost"),
                    "setup_cost": doc.get("setup_cost"),
                    "ported_from": doc.get("ported_from"),
                    "sip_username": doc.get("sip_username"),
                    "sip_password": doc.get("sip_password"),
                    "sip_server": doc.get("sip_server"),
                    "webhook_url": doc.get("webhook_url"),
                    "assigned_assistant_id": doc.get("assigned_assistant_id"),
                    "assigned_at": doc.get("assigned_at"),
                    # Cost tracking fields with defaults for existing records
                    "cost_per_minute": doc.get("cost_per_minute", 0.15),
                    "credit_balance": doc.get("credit_balance", 0.0),
                    "total_minutes_used": doc.get("total_minutes_used", 0.0),
                    "total_cost_spent": doc.get("total_cost_spent", 0.0),
                    "currency": doc.get("currency", "GHC"),
                    "low_balance_threshold": doc.get("low_balance_threshold"),
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "metadata": doc.get("metadata", {})
                }

                phone_number = PhoneNumber(**phone_data)
                self.phone_numbers[phone_number.id] = phone_number
                count += 1

            logger.info(f"Loaded {count} phone numbers from database")
        except Exception as e:
            logger.error(f"Error loading phone numbers from database: {e}")

    def _save_to_database(self, phone_number: PhoneNumber):
        """Save or update phone number in MongoDB"""
        if self.phone_numbers_collection is None:
            logger.warning("MongoDB not available - phone number will not persist")
            return

        try:
            # Convert PhoneNumber to dict for MongoDB
            phone_dict = phone_number.dict()

            # Use upsert to insert or update
            self.phone_numbers_collection.update_one(
                {"id": phone_number.id},
                {"$set": phone_dict},
                upsert=True
            )
            logger.debug(f"Saved phone number {phone_number.number} to database")
        except Exception as e:
            logger.error(f"Error saving phone number to database: {e}")

    def _delete_from_database(self, phone_number_id: str):
        """Delete phone number from MongoDB"""
        if self.phone_numbers_collection is None:
            logger.warning("MongoDB not available - deletion will not persist")
            return

        try:
            result = self.phone_numbers_collection.delete_one({"id": phone_number_id})
            if result.deleted_count > 0:
                logger.debug(f"Deleted phone number {phone_number_id} from database")
            else:
                logger.warning(f"Phone number {phone_number_id} not found in database")
        except Exception as e:
            logger.error(f"Error deleting phone number from database: {e}")

    def _save_credit_transaction(self, transaction: CreditTransaction):
        """Save credit transaction to MongoDB"""
        if self.credit_transactions_collection is None:
            logger.warning("MongoDB not available - transaction will not persist")
            return

        try:
            # Convert CreditTransaction to dict for MongoDB
            transaction_dict = transaction.dict()
            self.credit_transactions_collection.insert_one(transaction_dict)
            logger.debug(f"Saved credit transaction {transaction.id} to database")
        except Exception as e:
            logger.error(f"Error saving credit transaction to database: {e}")

    def add_credit(
        self,
        phone_number_id: str,
        amount: float,
        user_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> CreditTransaction:
        """
        Add credit to a phone number

        Args:
            phone_number_id: Phone number ID
            amount: Amount to add (positive value)
            user_id: User who added the credit
            payment_method: Payment method used
            reference_number: Payment reference number
            notes: Additional notes

        Returns:
            CreditTransaction object
        """
        if phone_number_id not in self.phone_numbers:
            raise HTTPException(status_code=404, detail="Phone number not found")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Credit amount must be positive")

        phone = self.phone_numbers[phone_number_id]
        balance_before = phone.credit_balance
        balance_after = balance_before + amount

        # Create transaction record
        transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        transaction = CreditTransaction(
            id=transaction_id,
            phone_id=phone.id,
            phone_number=phone.number,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            timestamp=datetime.utcnow(),
            balance_before=balance_before,
            balance_after=balance_after,
            added_by_user_id=user_id,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes
        )

        # Update phone balance
        phone.credit_balance = balance_after
        phone.updated_at = datetime.utcnow()

        # Save to database
        self._save_to_database(phone)
        self._save_credit_transaction(transaction)

        logger.info(f"Added {amount} {phone.currency} credit to {phone.number}. New balance: {balance_after}")

        return transaction

    def deduct_credit(
        self,
        phone_number_id: str,
        amount: float,
        call_id: Optional[str] = None,
        call_duration_seconds: Optional[int] = None,
        campaign_id: Optional[str] = None
    ) -> CreditTransaction:
        """
        Deduct credit from a phone number (for call usage)

        Args:
            phone_number_id: Phone number ID
            amount: Amount to deduct (positive value)
            call_id: Associated call ID
            call_duration_seconds: Call duration in seconds
            campaign_id: Associated campaign ID

        Returns:
            CreditTransaction object
        """
        if phone_number_id not in self.phone_numbers:
            raise HTTPException(status_code=404, detail="Phone number not found")

        if amount < 0:
            raise HTTPException(status_code=400, detail="Deduction amount must be positive")

        phone = self.phone_numbers[phone_number_id]
        balance_before = phone.credit_balance
        balance_after = balance_before - amount

        # Check for negative balance
        if balance_after < 0:
            logger.warning(f"Insufficient credit for {phone.number}. Balance: {balance_before}, Required: {amount}")
            # Allow negative balance but log warning
            # Could also raise exception here if strict enforcement needed

        # Calculate duration in minutes
        call_duration_minutes = None
        if call_duration_seconds is not None:
            call_duration_minutes = call_duration_seconds / 60.0

        # Create transaction record
        transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        transaction = CreditTransaction(
            id=transaction_id,
            phone_id=phone.id,
            phone_number=phone.number,
            amount=-amount,  # Negative for debit
            transaction_type=TransactionType.DEBIT,
            timestamp=datetime.utcnow(),
            balance_before=balance_before,
            balance_after=balance_after,
            call_id=call_id,
            call_duration_seconds=call_duration_seconds,
            call_duration_minutes=call_duration_minutes,
            campaign_id=campaign_id
        )

        # Update phone metrics
        phone.credit_balance = balance_after
        phone.total_cost_spent += amount
        if call_duration_minutes:
            phone.total_minutes_used += call_duration_minutes
        phone.updated_at = datetime.utcnow()

        # Save to database
        self._save_to_database(phone)
        self._save_credit_transaction(transaction)

        logger.info(f"Deducted {amount} {phone.currency} from {phone.number}. New balance: {balance_after}")

        # Check if balance fell below threshold and send alert (asynchronously)
        # Note: This creates a task but doesn't wait for it to complete
        import asyncio
        if balance_after < phone.low_balance_threshold and balance_before >= phone.low_balance_threshold:
            # Balance just crossed below threshold
            asyncio.create_task(self.send_low_balance_alert(phone, balance_after))
            logger.warning(f"Low balance alert triggered for {phone.number}: {balance_after} {phone.currency} < {phone.low_balance_threshold} {phone.currency}")

        return transaction

    def get_credit_history(
        self,
        phone_number_id: str,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None
    ) -> List[CreditTransaction]:
        """Get credit transaction history for a phone number"""
        if self.credit_transactions_collection is None:
            logger.warning("MongoDB not available - cannot retrieve credit history")
            return []

        if phone_number_id not in self.phone_numbers:
            raise HTTPException(status_code=404, detail="Phone number not found")

        try:
            # Build query
            query = {"phone_id": phone_number_id}
            if transaction_type:
                query["transaction_type"] = transaction_type

            # Fetch transactions
            transactions = []
            for doc in self.credit_transactions_collection.find(query).sort("timestamp", -1).limit(limit):
                transaction = CreditTransaction(**doc)
                transactions.append(transaction)

            return transactions
        except Exception as e:
            logger.error(f"Error retrieving credit history: {e}")
            return []

    async def import_from_twilio(self, config: ProviderConfig) -> List[PhoneNumber]:
        """Import phone numbers from Twilio"""
        await self.initialize()
        
        try:
            auth = aiohttp.BasicAuth(config.account_sid, config.auth_token)
            url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}/IncomingPhoneNumbers.json"
            
            async with self.session.get(url, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    numbers = []
                    
                    for twilio_number in data.get("incoming_phone_numbers", []):
                        phone_number = PhoneNumber(
                            id=twilio_number["sid"],
                            number=twilio_number["phone_number"],
                            provider=PhoneProvider.TWILIO,
                            type=PhoneNumberType.BOTH,
                            status=PhoneNumberStatus.ACTIVE,
                            country=twilio_number.get("address_requirements", "none"),
                            country_code=twilio_number["phone_number"][:3],
                            capabilities=self._extract_twilio_capabilities(twilio_number),
                            monthly_cost=float(twilio_number.get("monthly_cost", 0)),
                            created_at=datetime.fromisoformat(twilio_number["date_created"]),
                            updated_at=datetime.fromisoformat(twilio_number["date_updated"]),
                            metadata={"twilio_sid": twilio_number["sid"]}
                        )
                        numbers.append(phone_number)
                        self.phone_numbers[phone_number.id] = phone_number
                        self._save_to_database(phone_number)
                    
                    return numbers
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to import from Twilio: {await response.text()}"
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Twilio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def import_from_vonage(self, config: ProviderConfig) -> List[PhoneNumber]:
        """Import phone numbers from Vonage (Nexmo)"""
        await self.initialize()
        
        try:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            url = "https://api.nexmo.com/v2/applications"
            
            # First get applications
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    # Then get numbers
                    numbers_url = "https://rest.nexmo.com/account/numbers"
                    params = {
                        "api_key": config.api_key,
                        "api_secret": config.api_secret
                    }
                    
                    async with self.session.get(numbers_url, params=params) as num_response:
                        if num_response.status == 200:
                            data = await num_response.json()
                            numbers = []
                            
                            for vonage_number in data.get("numbers", []):
                                phone_number = PhoneNumber(
                                    id=vonage_number["msisdn"],
                                    number=f"+{vonage_number['msisdn']}",
                                    provider=PhoneProvider.VONAGE,
                                    type=self._get_vonage_type(vonage_number),
                                    status=PhoneNumberStatus.ACTIVE,
                                    country=vonage_number["country"],
                                    country_code=f"+{vonage_number['country'][:2]}",
                                    capabilities=vonage_number.get("features", []),
                                    monthly_cost=2.50,  # Default Vonage pricing
                                    created_at=datetime.utcnow(),
                                    updated_at=datetime.utcnow(),
                                    metadata={"vonage_id": vonage_number["msisdn"]}
                                )
                                numbers.append(phone_number)
                                self.phone_numbers[phone_number.id] = phone_number
                                self._save_to_database(phone_number)
                            
                            return numbers
                        else:
                            raise HTTPException(
                                status_code=num_response.status,
                                detail=f"Failed to get Vonage numbers"
                            )
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to authenticate with Vonage"
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Vonage: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def import_from_telnyx(self, config: ProviderConfig) -> List[PhoneNumber]:
        """Import phone numbers from Telnyx"""
        await self.initialize()
        
        try:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            url = "https://api.telnyx.com/v2/phone_numbers"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    numbers = []
                    
                    for telnyx_number in data.get("data", []):
                        phone_number = PhoneNumber(
                            id=telnyx_number["id"],
                            number=telnyx_number["phone_number"],
                            provider=PhoneProvider.TELNYX,
                            type=PhoneNumberType.BOTH,
                            status=self._get_telnyx_status(telnyx_number["status"]),
                            country=telnyx_number.get("country_code", "US"),
                            country_code=f"+{telnyx_number.get('country_code', '1')}",
                            capabilities=telnyx_number.get("capabilities", []),
                            monthly_cost=float(telnyx_number.get("monthly_recurring_cost", 0)),
                            created_at=datetime.fromisoformat(telnyx_number["created_at"]),
                            updated_at=datetime.fromisoformat(telnyx_number["updated_at"]),
                            metadata={"telnyx_id": telnyx_number["id"]}
                        )
                        numbers.append(phone_number)
                        self.phone_numbers[phone_number.id] = phone_number
                        self._save_to_database(phone_number)
                    
                    return numbers
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to import from Telnyx"
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Telnyx: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def import_from_vapi(self, config: ProviderConfig) -> List[PhoneNumber]:
        """Import phone number from VAPI by phone ID"""
        await self.initialize()

        try:
            # Get VAPI credentials from environment
            vapi_api_key = os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY")
            if not vapi_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="VAPI_PRIVATE_KEY not configured in environment"
                )

            # config should contain phone_id
            phone_id = config.phone_id
            if not phone_id:
                raise HTTPException(
                    status_code=400,
                    detail="VAPI phone_id is required"
                )

            vapi_base_url = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")
            headers = {
                "Authorization": f"Bearer {vapi_api_key}",
                "Content-Type": "application/json"
            }
            url = f"{vapi_base_url}/phone-number/{phone_id}"

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    vapi_phone = await response.json()

                    # Parse the phone number
                    phone_num = vapi_phone.get("number", "")
                    country_code = ""
                    if phone_num.startswith("+"):
                        # Extract country code (assume 1-3 digits)
                        for i in range(1, min(5, len(phone_num))):
                            if not phone_num[i].isdigit():
                                break
                            country_code = phone_num[:i+1]

                    # Map VAPI provider to country code
                    country = "GH" if "+233" in phone_num else "US"

                    # Create phone number object
                    phone_number = PhoneNumber(
                        id=f"vapi_{vapi_phone['id']}",
                        number=phone_num,
                        provider=PhoneProvider.VAPI,
                        type=PhoneNumberType.BOTH,
                        status=PhoneNumberStatus.ACTIVE,
                        country=country,
                        country_code=country_code or "+1",
                        capabilities=["voice"],
                        monthly_cost=0.0,  # VAPI uses per-minute billing
                        cost_per_minute=0.15 if country == "GH" else 0.01,  # Default rates
                        credit_balance=0.0,
                        currency="GHC" if country == "GH" else "USD",
                        created_at=datetime.fromisoformat(vapi_phone["createdAt"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(vapi_phone["updatedAt"].replace("Z", "+00:00")),
                        metadata={
                            "vapi_id": vapi_phone["id"],
                            "vapi_provider": vapi_phone.get("provider"),
                            "vapi_name": vapi_phone.get("name"),
                            "byo_phone": True
                        }
                    )

                    # Save to database
                    self.phone_numbers[phone_number.id] = phone_number
                    self._save_to_database(phone_number)

                    logger.info(f"Imported VAPI phone number: {phone_num} (ID: {phone_id})")
                    return [phone_number]

                elif response.status == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Phone number not found in VAPI with ID: {phone_id}"
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"VAPI API error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch phone number from VAPI: {error_text}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to VAPI: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def provision_kasaai_number(
        self,
        country_code: str,
        area_code: Optional[str] = None,
        plan: str = "starter",
        sip_provider: str = "freeswitch"
    ) -> PhoneNumber:
        """Provision a virtual number through Kasaai/Asterisk"""
        
        # Generate virtual number based on country and area code
        if country_code == "+233":  # Ghana
            prefixes = {
                "mtn": ["024", "054", "055", "059"],
                "vodafone": ["020", "050"],
                "airteltigo": ["026", "027", "056", "057"]
            }
            
            # Select appropriate prefix
            if area_code and area_code in sum(prefixes.values(), []):
                prefix = area_code
            else:
                prefix = "024"  # Default to MTN
            
            # Generate number
            number = f"{country_code}{prefix}{random.randint(1000000, 9999999)}"

        elif country_code == "+1":  # US/Canada
            area = area_code or "555"
            number = f"{country_code}{area}{random.randint(1000000, 9999999)}"
            
        else:
            # Generic international number
            number = f"{country_code}{random.randint(1000000000, 9999999999)}"
        
        # Create SIP credentials
        sip_username = f"kasaai_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        sip_password = self._generate_secure_password()
        
        # Determine pricing based on plan
        pricing = {
            "starter": 1.00,
            "professional": 5.00,
            "enterprise": 20.00
        }
        
        phone_number = PhoneNumber(
            id=f"kasaai_{sip_username}",
            number=number,
            provider=PhoneProvider.KASAAI,
            type=PhoneNumberType.BOTH,
            status=PhoneNumberStatus.PENDING,
            country=self._get_country_from_code(country_code),
            country_code=country_code,
            capabilities=["voice", "sms", "mms", "fax"],
            monthly_cost=pricing.get(plan, 1.00),
            setup_cost=0.00,
            sip_username=sip_username,
            sip_password=sip_password,
            sip_server="asterisk.ailabsafrica.com",
            webhook_url=f"https://api.kasaai.ailabsafrica.com/voice/webhook/{sip_username}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "plan": plan,
                "virtual": True,
                "sip_context": "kasaai-inbound",
                "sip_provider": sip_provider
            }
        )

        # Register with SIP server (FreeSWITCH or Asterisk)
        await self._register_with_sip_server(phone_number, preferred_provider=sip_provider)

        # Update status
        phone_number.status = PhoneNumberStatus.ACTIVE
        self.phone_numbers[phone_number.id] = phone_number

        # Save to database
        self._save_to_database(phone_number)

        return phone_number

    async def _register_with_sip_server(self, phone_number: PhoneNumber, preferred_provider: str = "freeswitch"):
        """Register virtual number with SIP server (FreeSWITCH or Asterisk)"""

        # Use specified provider
        if preferred_provider == "freeswitch" and self.freeswitch_client:
            logger.info(f"Registering {phone_number.number} with FreeSWITCH")
            try:
                # Create SIP peer via FreeSWITCH REST API
                response = await self.freeswitch_client.create_sip_peer(
                    number=phone_number.number,
                    sip_username=phone_number.sip_username,
                    sip_password=phone_number.sip_password,
                    webhook_url=phone_number.webhook_url,
                    context=phone_number.metadata.get("sip_context", "kasaai-inbound")
                )

                if response.get("success"):
                    logger.info(f"Successfully registered {phone_number.number} with FreeSWITCH")
                    logger.info(f"SIP credentials: {response.get('sip_credentials')}")
                    return True
                else:
                    logger.error(f"Failed to register {phone_number.number}: {response.get('message')}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to register with FreeSWITCH: {response.get('message')}"
                    )

            except Exception as e:
                logger.error(f"Error registering with FreeSWITCH: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to register with FreeSWITCH: {str(e)}"
                )

        # Use Asterisk if specified or as fallback
        elif preferred_provider == "asterisk" and self.asterisk_client:
            logger.info(f"Registering {phone_number.number} with Asterisk (user selected)")
            try:
                # Create SIP peer via Asterisk REST API
                response = await self.asterisk_client.create_sip_peer(
                    number=phone_number.number,
                    sip_username=phone_number.sip_username,
                    sip_password=phone_number.sip_password,
                    webhook_url=phone_number.webhook_url
                )

                if response.get("success"):
                    logger.info(f"Successfully registered {phone_number.number} with Asterisk")
                    logger.info(f"SIP credentials: {response.get('sip_credentials')}")
                    return True
                else:
                    logger.error(f"Failed to register {phone_number.number}: {response.get('message')}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to register with Asterisk: {response.get('message')}"
                    )

            except Exception as e:
                logger.error(f"Error registering with Asterisk: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to register with Asterisk: {str(e)}"
                )

        # Fallback if preferred provider not available
        elif preferred_provider == "asterisk" and self.freeswitch_client:
            logger.warning(f"Asterisk requested but not available, falling back to FreeSWITCH")
            return await self._register_with_sip_server(phone_number, preferred_provider="freeswitch")
        elif preferred_provider == "freeswitch" and self.asterisk_client:
            logger.warning(f"FreeSWITCH requested but not available, falling back to Asterisk")
            return await self._register_with_sip_server(phone_number, preferred_provider="asterisk")
        else:
            logger.warning("No SIP client available - simulating registration")
            return True

    async def _unregister_from_sip_server(self, phone_number: PhoneNumber):
        """Unregister virtual number from SIP server (FreeSWITCH or Asterisk)"""

        # Try FreeSWITCH first (preferred)
        if self.freeswitch_client:
            logger.info(f"Unregistering {phone_number.number} from FreeSWITCH")
            try:
                # Delete SIP peer via FreeSWITCH REST API
                response = await self.freeswitch_client.delete_sip_peer(
                    number=phone_number.number,
                    sip_username=phone_number.sip_username
                )

                if response.get("success"):
                    logger.info(f"Successfully unregistered {phone_number.number} from FreeSWITCH")
                    return True
                else:
                    logger.warning(f"Failed to unregister {phone_number.number}: {response.get('message')}")
                    return False

            except Exception as e:
                logger.error(f"Error unregistering from FreeSWITCH: {e}")
                return False

        # Fallback to Asterisk (deprecated)
        elif self.asterisk_client:
            logger.info(f"Unregistering {phone_number.number} from Asterisk (deprecated)")
            try:
                # Delete SIP peer via Asterisk REST API
                response = await self.asterisk_client.delete_sip_peer(
                    number=phone_number.number,
                    sip_username=phone_number.sip_username
                )

                if response.get("success"):
                    logger.info(f"Successfully unregistered {phone_number.number} from Asterisk")
                    return True
                else:
                    logger.warning(f"Failed to unregister {phone_number.number}: {response.get('message')}")
                    return False

            except Exception as e:
                logger.error(f"Error unregistering from Asterisk: {e}")
                return False

        else:
            logger.warning("No SIP client available - simulating unregistration")
            return True
    
    def _extract_twilio_capabilities(self, twilio_number: Dict) -> List[str]:
        """Extract capabilities from Twilio number"""
        capabilities = []
        if twilio_number.get("capabilities", {}).get("voice"):
            capabilities.append("voice")
        if twilio_number.get("capabilities", {}).get("sms"):
            capabilities.append("sms")
        if twilio_number.get("capabilities", {}).get("mms"):
            capabilities.append("mms")
        if twilio_number.get("capabilities", {}).get("fax"):
            capabilities.append("fax")
        return capabilities
    
    def _get_vonage_type(self, vonage_number: Dict) -> PhoneNumberType:
        """Determine Vonage number type"""
        features = vonage_number.get("features", [])
        if "VOICE" in features and "SMS" in features:
            return PhoneNumberType.BOTH
        elif "VOICE" in features:
            return PhoneNumberType.INBOUND
        else:
            return PhoneNumberType.OUTBOUND
    
    def _get_telnyx_status(self, status: str) -> PhoneNumberStatus:
        """Map Telnyx status to our status"""
        status_map = {
            "active": PhoneNumberStatus.ACTIVE,
            "inactive": PhoneNumberStatus.INACTIVE,
            "pending": PhoneNumberStatus.PENDING,
            "porting": PhoneNumberStatus.PORTING
        }
        return status_map.get(status.lower(), PhoneNumberStatus.INACTIVE)
    
    def _get_country_from_code(self, country_code: str) -> str:
        """Get country name from country code"""
        country_map = {
            "+1": "US",
            "+44": "GB",
            "+233": "GH",
            "+234": "NG",
            "+254": "KE",
            "+27": "ZA",
            "+91": "IN",
            "+86": "CN"
        }
        return country_map.get(country_code, "INTL")
    
    def _generate_secure_password(self) -> str:
        """Generate secure password for SIP"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(16))


# Global phone number manager instance
phone_manager = PhoneNumberManager()


# API Routes

@router.get("/")
async def list_phone_numbers():
    """List all phone numbers"""
    return {
        "success": True,
        "count": len(phone_manager.phone_numbers),
        "numbers": list(phone_manager.phone_numbers.values())
    }


@router.post("/import")
async def import_phone_numbers(request: ImportRequest):
    """Import phone numbers from a provider"""
    try:
        numbers = []

        if request.provider == PhoneProvider.TWILIO:
            numbers = await phone_manager.import_from_twilio(request.config)
        elif request.provider == PhoneProvider.VONAGE:
            numbers = await phone_manager.import_from_vonage(request.config)
        elif request.provider == PhoneProvider.TELNYX:
            numbers = await phone_manager.import_from_telnyx(request.config)
        elif request.provider == PhoneProvider.VAPI:
            numbers = await phone_manager.import_from_vapi(request.config)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Import not supported for provider: {request.provider}"
            )
        
        return {
            "success": True,
            "message": f"Imported {len(numbers)} numbers from {request.provider}",
            "numbers": numbers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import numbers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/provision")
async def provision_phone_number(request: ProvisionRequest):
    """Provision a new phone number"""
    try:
        if request.provider == PhoneProvider.KASAAI:
            number = await phone_manager.provision_kasaai_number(
                country_code=request.country_code,
                area_code=request.area_code,
                plan=request.plan,
                sip_provider=request.sip_provider or "freeswitch"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Provisioning not implemented for provider: {request.provider}"
            )

        return {
            "success": True,
            "message": "Phone number provisioned successfully",
            "number": number
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to provision number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: Specific routes must come before generic /{number_id} route to avoid conflicts

@router.get("/providers/available")
async def get_available_providers():
    """Get list of available phone number providers"""
    return {
        "providers": [
            {
                "id": PhoneProvider.KASAAI,
                "name": "Kasa AI",
                "description": "Virtual numbers powered by Asterisk/FreeSWITCH",
                "features": ["Instant provisioning", "Low cost", "Global coverage"],
                "pricing": {
                    "starter": "$1/month",
                    "professional": "$5/month",
                    "enterprise": "$20/month"
                }
            },
            {
                "id": PhoneProvider.TWILIO,
                "name": "Twilio",
                "description": "Import your existing Twilio numbers",
                "features": ["SMS", "Voice", "MMS", "WhatsApp"],
                "requires": ["account_sid", "auth_token"]
            },
            {
                "id": PhoneProvider.VONAGE,
                "name": "Vonage",
                "description": "Import your existing Vonage numbers",
                "features": ["Global coverage", "Voice", "SMS"],
                "requires": ["api_key", "api_secret"]
            },
            {
                "id": PhoneProvider.TELNYX,
                "name": "Telnyx",
                "description": "Import your existing Telnyx numbers",
                "features": ["Mission critical", "Global network"],
                "requires": ["api_key"]
            },
            {
                "id": PhoneProvider.SIP_TRUNK,
                "name": "SIP Trunk",
                "description": "Configure your own SIP trunk",
                "features": ["Custom configuration", "Any provider"],
                "requires": ["sip_server", "sip_username", "sip_password"]
            }
        ]
    }


@router.get("/cost-summary")
async def get_cost_summary():
    """Get aggregated cost summary across all phone numbers with real-time data from MongoDB"""
    try:
        from ...mongo import get_database
        db = get_database()
        campaign_calls = db["campaign_calls"]
        automation_calls = db["automation_calls"]
        campaigns = db["automation_campaigns"]

        total_balance = 0.0
        total_minutes_used = 0.0
        total_cost_spent = 0.0
        low_balance_count = 0

        phones_with_credit = []

        # Build a map of phone usage from MongoDB collections
        phone_usage_map = {}

        # Aggregate from campaign_calls collection
        # IMPORTANT: Only track VAPI AI service costs (GPT-4, voice synthesis, etc.)
        # Phone costs are tracked ONLY by Asterisk CDR - NOT by VAPI
        # This prevents double-counting and ensures accurate phone cost tracking
        campaign_calls_pipeline = [
            {
                "$match": {
                    # Include all completed call statuses from VAPI
                    "status": {"$in": ["completed", "ended", "customer-ended-call", "assistant-ended-call"]},
                    "cost": {"$exists": True, "$gt": 0}  # Only track calls with AI service costs
                }
            },
            {
                "$lookup": {
                    "from": "automation_campaigns",
                    "localField": "campaign_id",
                    "foreignField": "_id",
                    "as": "campaign_info"
                }
            },
            {
                "$unwind": {"path": "$campaign_info", "preserveNullAndEmptyArrays": True}
            },
            {
                "$group": {
                    "_id": "$campaign_info.phone_id",
                    "total_vapi_cost_usd": {"$sum": "$cost"},  # VAPI AI service costs only (GPT-4, voice, etc.)
                    "vapi_call_count": {"$sum": 1}
                    # NOTE: We do NOT track duration here - Asterisk CDR is the source of truth for phone minutes
                }
            }
        ]

        async for result in campaign_calls.aggregate(campaign_calls_pipeline):
            phone_id = result.get("_id")
            if phone_id:
                # Only store VAPI AI service costs - phone costs come from Asterisk CDR
                phone_usage_map[phone_id] = {
                    "total_vapi_cost_usd": result.get("total_vapi_cost_usd", 0),  # VAPI AI service charges only
                    "vapi_call_count": result.get("vapi_call_count", 0)
                }

        # Aggregate from asterisk_calls collection (Asterisk CDR data)
        # This is the PRIMARY source of truth for phone costs and minutes
        asterisk_calls = db["asterisk_calls"]
        asterisk_pipeline = [
            {
                "$match": {
                    "disposition": "ANSWERED",  # Only count answered calls for billing
                    "billsec_seconds": {"$exists": True, "$gt": 0},  # Must have billable seconds
                    "phone_id": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$phone_id",
                    "total_asterisk_minutes": {"$sum": {"$divide": ["$billsec_seconds", 60]}},  # Convert seconds to minutes
                    "total_asterisk_cost_ghc": {"$sum": "$cost_ghc"},
                    "asterisk_call_count": {"$sum": 1}
                }
            }
        ]

        async for result in asterisk_calls.aggregate(asterisk_pipeline):
            phone_id = result.get("_id")
            if phone_id:
                asterisk_minutes = result.get("total_asterisk_minutes", 0)
                asterisk_cost = result.get("total_asterisk_cost_ghc", 0)
                asterisk_calls = result.get("asterisk_call_count", 0)
                
                # Merge with existing usage or create new entry
                if phone_id in phone_usage_map:
                    # Phone uses Asterisk - prioritize Asterisk data for phone costs
                    # VAPI data is only for AI service costs
                    phone_usage_map[phone_id]["total_minutes"] = asterisk_minutes  # Use Asterisk minutes (not VAPI)
                    phone_usage_map[phone_id]["asterisk_minutes"] = asterisk_minutes
                    phone_usage_map[phone_id]["asterisk_cost_ghc"] = asterisk_cost
                    phone_usage_map[phone_id]["asterisk_call_count"] = asterisk_calls
                    # Keep VAPI cost for AI services
                else:
                    # Asterisk-only phone (no VAPI data)
                    phone_usage_map[phone_id] = {
                        "total_vapi_cost_usd": 0,  # No VAPI AI costs
                        "total_minutes": asterisk_minutes,  # Use Asterisk minutes
                        "call_count": asterisk_calls,
                        "asterisk_minutes": asterisk_minutes,
                        "asterisk_cost_ghc": asterisk_cost,
                        "asterisk_call_count": asterisk_calls
                    }

        # Get fresh phone data from MongoDB for real-time balances
        phones_collection = db["managed_phone_numbers"]
        fresh_phones_cursor = phones_collection.find({})
        fresh_phones = await fresh_phones_cursor.to_list(length=100)
        fresh_phone_map = {p.get("id"): p for p in fresh_phones}

        # Iterate over phone_manager to get phone details and merge with usage data
        for phone in phone_manager.phone_numbers.values():
            # Try both with and without provider prefix (e.g., "vapi_6d828206..." and "6d828206...")
            phone_id_without_prefix = phone.id.replace(f"{phone.provider}_", "") if "_" in phone.id else phone.id

            # Check both phone.id and id without prefix
            usage = phone_usage_map.get(phone.id, phone_usage_map.get(phone_id_without_prefix, {}))

            # Get fresh phone data from MongoDB for real-time balance
            fresh_phone = fresh_phone_map.get(phone.id, {})

            # Get VAPI cost (AI service costs only - GPT-4, voice synthesis, etc.)
            vapi_cost_usd = usage.get("total_vapi_cost_usd", 0)
            
            # Get Asterisk-specific costs (phone costs at 0.15 GHC/min)
            asterisk_cost_ghc = usage.get("asterisk_cost_ghc", 0)
            asterisk_minutes = usage.get("asterisk_minutes", 0)
            
            # Smart cost calculation:
            # - If Asterisk data exists: Use Asterisk for phone costs (accurate 0.15 GHC/min) - PRIMARY SOURCE
            # - If no Asterisk data: This is a VAPI-only number (not through Asterisk), skip phone cost tracking
            if asterisk_cost_ghc > 0:
                # Phone uses Asterisk - use Asterisk data for phone costs (PRIMARY SOURCE)
                phone_cost_ghc = asterisk_cost_ghc
                phone_total_minutes = asterisk_minutes
            else:
                # VAPI-only number (not through Asterisk proxy)
                # For these numbers, we don't track phone costs separately - they're handled by VAPI
                # Only show VAPI AI service costs
                phone_total_minutes = 0  # Don't track minutes for VAPI-only numbers in phone cost context
                phone_cost_ghc = 0  # Phone costs not tracked for VAPI-only numbers

            # Get credit balance from FRESH MongoDB data (not cached)
            credit_balance = fresh_phone.get("credit_balance", phone.credit_balance)
            total_minutes_from_db = fresh_phone.get("total_minutes_used", 0)
            total_cost_from_db = fresh_phone.get("total_cost_spent", 0)

            # Calculate remaining minutes based on fresh credit balance
            remaining_minutes = (credit_balance / phone.cost_per_minute) if phone.cost_per_minute > 0 else 0
            
            # Low balance alert: if remaining minutes < 1000 minutes (about 16.7 hours at 0.15 GHC/min = 150 GHC)
            # Or if balance is below threshold
            low_balance_threshold_minutes = 1000  # ~150 GHC worth of minutes
            is_low_balance = False
            if phone.low_balance_threshold:
                is_low_balance = credit_balance < phone.low_balance_threshold
            else:
                is_low_balance = remaining_minutes < low_balance_threshold_minutes

            total_balance += credit_balance
            total_minutes_used += phone_total_minutes
            total_cost_spent += phone_cost_ghc  # Track phone billing costs

            if is_low_balance:
                low_balance_count += 1

            # Include phones with activity OR VAPI/BYO phones (so they can have credit added)
            is_vapi_or_byo = phone.provider == PhoneProvider.VAPI or phone.metadata.get("byo_phone", False)
            has_activity = credit_balance > 0 or phone_total_minutes > 0

            if has_activity or is_vapi_or_byo:
                # Use MAX of asterisk aggregation or MongoDB stored values for minutes/cost
                # This ensures both real-time aggregation AND pre-stored totals are considered
                display_minutes = max(phone_total_minutes, total_minutes_from_db)
                display_cost = max(phone_cost_ghc, total_cost_from_db)

                phones_with_credit.append({
                    "id": phone.id,
                    "number": phone.number,
                    "provider": phone.provider,
                    "currency": phone.currency,
                    "credit_balance": round(credit_balance, 2),  # Fresh from MongoDB
                    "total_minutes_used": round(display_minutes, 2),
                    "total_cost_spent": round(display_cost, 2),  # Phone billing cost (GHC)
                    "vapi_cost_usd": round(vapi_cost_usd, 2),  # VAPI platform cost (USD)
                    "cost_per_minute": phone.cost_per_minute,
                    "remaining_minutes": round((credit_balance / phone.cost_per_minute) if phone.cost_per_minute > 0 else 0, 1),
                    "low_balance_alert": is_low_balance
                })

        logger.info(f"📊 Cost summary generated: {len(phones_with_credit)} phones with activity, total phone cost: GHC {total_cost_spent:.2f}, total minutes: {total_minutes_used:.1f}")

        return {
            "success": True,
            "summary": {
                "total_phones": len(phone_manager.phone_numbers),
                "phones_with_activity": len(phones_with_credit),
                "total_balance": round(total_balance, 2),
                "total_minutes_used": round(total_minutes_used, 2),
                "total_cost_spent": round(total_cost_spent, 2),
                "low_balance_alerts": low_balance_count
            },
            "phones": phones_with_credit
        }

    except Exception as e:
        logger.error(f"Failed to generate cost summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/{assistant_id}")
async def get_assistant_phone_numbers(assistant_id: str):
    """Get all phone numbers assigned to an assistant"""
    assigned_numbers = [
        number for number in phone_manager.phone_numbers.values()
        if number.assigned_assistant_id == assistant_id
    ]

    return {
        "success": True,
        "assistant_id": assistant_id,
        "count": len(assigned_numbers),
        "numbers": assigned_numbers
    }


@router.get("/{number_id}")
async def get_phone_number(number_id: str):
    """Get details of a specific phone number"""
    if number_id in phone_manager.phone_numbers:
        return phone_manager.phone_numbers[number_id]
    else:
        raise HTTPException(status_code=404, detail="Phone number not found")


@router.delete("/{number_id}")
async def delete_phone_number(number_id: str):
    """Delete/release a phone number"""
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    number = phone_manager.phone_numbers[number_id]

    # Unregister from SIP server if it's a Kasaai number
    if number.provider == PhoneProvider.KASAAI:
        try:
            await phone_manager._unregister_from_sip_server(number)
        except Exception as e:
            logger.warning(f"Failed to unregister from SIP server: {e}")
            # Continue with deletion even if unregistration fails

    del phone_manager.phone_numbers[number_id]

    # Delete from database
    phone_manager._delete_from_database(number_id)

    return {
        "success": True,
        "message": "Phone number deleted",
        "number": number.number
    }


@router.post("/{number_id}/configure")
async def configure_phone_number(
    number_id: str,
    webhook_url: Optional[str] = None,
    sip_config: Optional[Dict[str, Any]] = None
):
    """Configure a phone number's settings"""
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    number = phone_manager.phone_numbers[number_id]
    
    if webhook_url:
        number.webhook_url = webhook_url
    
    if sip_config:
        number.sip_server = sip_config.get("server", number.sip_server)
        number.sip_username = sip_config.get("username", number.sip_username)
        number.sip_password = sip_config.get("password", number.sip_password)

    number.updated_at = datetime.utcnow()

    # Save to database
    phone_manager._save_to_database(number)

    return {
        "success": True,
        "message": "Phone number configured",
        "number": number
    }


# Phone-to-Assistant Assignment Endpoints

class AssignRequest(BaseModel):
    """Request to assign phone number to assistant"""
    assistant_id: str


@router.post("/{number_id}/assign")
async def assign_phone_to_assistant(number_id: str, request: AssignRequest):
    """
    Assign a phone number to an assistant (one-to-one mapping).
    If the phone is already assigned to another assistant, it will be unassigned first.
    If the assistant already has this phone assigned, it will be removed from assignment.
    """
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    number = phone_manager.phone_numbers[number_id]

    # Check if phone is already assigned to a different assistant
    if number.assigned_assistant_id and number.assigned_assistant_id != request.assistant_id:
        # Unassign from old assistant first
        old_assistant_id = number.assigned_assistant_id
        logger.info(f"Phone {number.number} was assigned to {old_assistant_id}, unassigning first")

    # Check if trying to unassign (clicking same assistant)
    if number.assigned_assistant_id == request.assistant_id:
        # Unassign
        number.assigned_assistant_id = None
        number.assigned_at = None
        number.updated_at = datetime.utcnow()

        # Save to database
        phone_manager._save_to_database(number)

        return {
            "success": True,
            "message": "Phone number unassigned from assistant",
            "number": number,
            "action": "unassigned"
        }

    # Assign to new assistant
    number.assigned_assistant_id = request.assistant_id
    number.assigned_at = datetime.utcnow()
    number.updated_at = datetime.utcnow()

    # Save to database
    phone_manager._save_to_database(number)

    return {
        "success": True,
        "message": "Phone number assigned to assistant",
        "number": number,
        "action": "assigned"
    }


@router.delete("/{number_id}/unassign")
async def unassign_phone_from_assistant(number_id: str):
    """Unassign a phone number from its assistant"""
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    number = phone_manager.phone_numbers[number_id]

    if not number.assigned_assistant_id:
        raise HTTPException(status_code=400, detail="Phone number is not assigned to any assistant")

    number.assigned_assistant_id = None
    number.assigned_at = None
    number.updated_at = datetime.utcnow()

    # Save to database
    phone_manager._save_to_database(number)

    return {
        "success": True,
        "message": "Phone number unassigned",
        "number": number
    }


# Credit Management Endpoints

class AddCreditRequest(BaseModel):
    """Request to add credit to a phone number"""
    amount: float = Field(..., gt=0, description="Amount to add (must be positive)")
    user_id: Optional[str] = Field(None, description="User who added the credit")
    payment_method: Optional[str] = Field(None, description="Payment method (cash, mobile_money, bank_transfer, etc.)")
    reference_number: Optional[str] = Field(None, description="Payment reference number")
    notes: Optional[str] = Field(None, description="Additional notes")


class UpdateCostRateRequest(BaseModel):
    """Request to update cost per minute rate"""
    cost_per_minute: float = Field(..., ge=0, description="Cost per minute in local currency")
    currency: Optional[str] = Field(None, description="Currency code (GHC, USD, etc.)")
    low_balance_threshold: Optional[float] = Field(None, description="Alert threshold for low balance")


@router.post("/{number_id}/credit")
async def add_phone_credit(number_id: str, request: AddCreditRequest):
    """Add credit to a phone number"""
    try:
        transaction = phone_manager.add_credit(
            phone_number_id=number_id,
            amount=request.amount,
            user_id=request.user_id,
            payment_method=request.payment_method,
            reference_number=request.reference_number,
            notes=request.notes
        )

        # Get updated phone number
        phone = phone_manager.phone_numbers[number_id]

        return {
            "success": True,
            "message": f"Added {request.amount} {phone.currency} credit successfully",
            "transaction": transaction,
            "phone": phone
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add credit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{number_id}/credit-history")
async def get_phone_credit_history(
    number_id: str,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = None
):
    """Get credit transaction history for a phone number"""
    try:
        transactions = phone_manager.get_credit_history(
            phone_number_id=number_id,
            limit=limit,
            transaction_type=transaction_type
        )

        return {
            "success": True,
            "count": len(transactions),
            "transactions": transactions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve credit history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{number_id}/usage-stats")
async def get_phone_usage_stats(number_id: str):
    """Get usage statistics for a phone number"""
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    phone = phone_manager.phone_numbers[number_id]

    # Calculate remaining credit in minutes
    remaining_minutes = 0.0
    if phone.cost_per_minute > 0:
        remaining_minutes = phone.credit_balance / phone.cost_per_minute

    # Get recent transactions
    recent_transactions = phone_manager.get_credit_history(phone_number_id=number_id, limit=10)

    # Calculate percentage of balance used
    total_added = sum(t.amount for t in recent_transactions if t.transaction_type == TransactionType.CREDIT)
    usage_percentage = 0.0
    if total_added > 0:
        usage_percentage = (phone.total_cost_spent / total_added) * 100

    return {
        "success": True,
        "phone_id": phone.id,
        "phone_number": phone.number,
        "currency": phone.currency,
        "cost_per_minute": phone.cost_per_minute,
        "credit_balance": phone.credit_balance,
        "remaining_minutes": round(remaining_minutes, 2),
        "total_minutes_used": round(phone.total_minutes_used, 2),
        "total_cost_spent": round(phone.total_cost_spent, 2),
        "usage_percentage": round(usage_percentage, 2),
        "low_balance_alert": phone.low_balance_threshold is not None and phone.credit_balance < phone.low_balance_threshold,
        "low_balance_threshold": phone.low_balance_threshold,
        "recent_transactions_count": len(recent_transactions)
    }


@router.put("/{number_id}/cost-rate")
async def update_phone_cost_rate(number_id: str, request: UpdateCostRateRequest):
    """Update cost per minute rate for a phone number"""
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    try:
        phone = phone_manager.phone_numbers[number_id]

        # Update cost rate
        phone.cost_per_minute = request.cost_per_minute

        if request.currency:
            phone.currency = request.currency

        if request.low_balance_threshold is not None:
            phone.low_balance_threshold = request.low_balance_threshold

        phone.updated_at = datetime.utcnow()

        # Save to database
        phone_manager._save_to_database(phone)

        return {
            "success": True,
            "message": "Cost rate updated successfully",
            "phone": phone
        }

    except Exception as e:
        logger.error(f"Failed to update cost rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Low Credit Alert Endpoints

@router.post("/alerts/test")
async def test_low_credit_alert():
    """
    Send a test low credit alert email to verify the notification system.
    This sends to alfred.anyan@gmail.com.
    """
    try:
        if LOW_CREDIT_NOTIFIER_AVAILABLE:
            notifier = get_low_credit_notifier()
            success = await notifier.send_test_notification(
                recipient_email="alfred.anyan@gmail.com"
            )

            if success:
                return {
                    "success": True,
                    "message": "Test alert sent successfully to alfred.anyan@gmail.com",
                    "method": "unified_notifier"
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to send test alert via notifier"
                )
        else:
            # Fallback test
            return {
                "success": False,
                "message": "LowCreditNotifier not available, please check shared services",
                "method": "fallback_unavailable"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{number_id}/alerts/trigger")
async def trigger_low_credit_alert(number_id: str):
    """
    Manually trigger a low credit alert for a specific phone number.
    Useful for testing or forcing an alert to be sent.
    """
    if number_id not in phone_manager.phone_numbers:
        raise HTTPException(status_code=404, detail="Phone number not found")

    try:
        phone = phone_manager.phone_numbers[number_id]

        if LOW_CREDIT_NOTIFIER_AVAILABLE:
            notifier = get_low_credit_notifier()
            success = await notifier.send_low_credit_alert(
                phone_number=phone.number,
                phone_id=phone.id,
                provider=phone.provider.value if hasattr(phone.provider, 'value') else str(phone.provider),
                current_balance=phone.credit_balance,
                threshold=phone.low_balance_threshold,
                currency=phone.currency,
                cost_per_minute=phone.cost_per_minute,
                recipient_email="alfred.anyan@gmail.com"
            )

            if success:
                return {
                    "success": True,
                    "message": f"Low credit alert triggered for {phone.number}",
                    "phone_id": phone.id,
                    "current_balance": phone.credit_balance,
                    "threshold": phone.low_balance_threshold,
                    "recipient": "alfred.anyan@gmail.com"
                }
            else:
                return {
                    "success": False,
                    "message": "Alert not sent (may be in cooldown period)",
                    "phone_id": phone.id
                }
        else:
            # Use fallback
            await phone_manager._send_low_balance_alert_fallback(phone, phone.credit_balance)
            return {
                "success": True,
                "message": f"Low credit alert triggered via fallback for {phone.number}",
                "phone_id": phone.id,
                "method": "fallback"
            }

    except Exception as e:
        logger.error(f"Failed to trigger alert for {number_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Slack Alert Endpoints

class SlackLowCreditAlertRequest(BaseModel):
    """Request to send Slack alert for low credit"""
    phone_number: str = Field(..., description="Phone number")
    current_balance: float = Field(..., description="Current credit balance")
    threshold: float = Field(default=500.0, description="Alert threshold (default: 500 GHC)")
    currency: str = Field(default="GHC", description="Currency code")
    phone_name: Optional[str] = Field(None, description="Optional friendly name")
    remaining_minutes: Optional[float] = Field(None, description="Remaining call minutes")


@router.post("/alerts/slack/low-credit")
async def send_slack_low_credit_alert(request: SlackLowCreditAlertRequest):
    """
    Send a Slack notification for low phone credit.
    This endpoint should be called when credit falls below the threshold (default: 500 GHC).
    """
    try:
        from ...services.slack_notification_service import slack_notification_service

        result = await slack_notification_service.send_low_credit_alert(
            phone_number=request.phone_number,
            current_balance=request.current_balance,
            threshold=request.threshold,
            currency=request.currency,
            phone_name=request.phone_name,
            remaining_minutes=request.remaining_minutes
        )

        if result.get("success"):
            if result.get("skipped"):
                return {
                    "success": True,
                    "message": "Alert skipped (cooldown active - already sent within the hour)",
                    "skipped": True
                }
            return {
                "success": True,
                "message": f"Slack alert sent for {request.phone_number}",
                "phone_number": request.phone_number,
                "balance": request.current_balance,
                "threshold": request.threshold
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send Slack alert: {result.get('error')}"
            )

    except ImportError as e:
        logger.error(f"Slack notification service not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="Slack notification service not configured"
        )
    except Exception as e:
        logger.error(f"Failed to send Slack low credit alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/slack/critical-balance")
async def send_slack_critical_balance_alert(
    total_balance: float,
    threshold: float = 500.0,
    currency: str = "GHC",
    phones_below_threshold: int = 0
):
    """
    Send a critical Slack alert when total system balance is low.
    """
    try:
        from ...services.slack_notification_service import slack_notification_service

        result = await slack_notification_service.send_critical_balance_alert(
            total_balance=total_balance,
            threshold=threshold,
            currency=currency,
            phones_below_threshold=phones_below_threshold
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "Critical balance Slack alert sent",
                "total_balance": total_balance,
                "threshold": threshold
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send critical alert: {result.get('error')}"
            )

    except ImportError as e:
        logger.error(f"Slack notification service not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="Slack notification service not configured"
        )
    except Exception as e:
        logger.error(f"Failed to send critical balance alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))