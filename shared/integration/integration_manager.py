"""
Integration Capabilities

This module provides integration capabilities including:
- CRM integrations (Salesforce, HubSpot)
- ERP system integration
- Payment gateway integration
- Third-party API marketplace
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import hmac
import base64
from urllib.parse import urlencode, urljoin
import aiohttp
from pathlib import Path

# Optional advanced libraries
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("Stripe library not available. Install stripe for payment gateway integration.")

try:
    import simple_salesforce
    SALESFORCE_AVAILABLE = True
except ImportError:
    SALESFORCE_AVAILABLE = False
    logging.warning("Salesforce library not available. Install simple-salesforce for CRM integration.")


class IntegrationType(Enum):
    """Integration types"""
    CRM = "crm"
    ERP = "erp"
    PAYMENT = "payment"
    MARKETPLACE = "marketplace"
    CUSTOM = "custom"


class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CONFIGURING = "configuring"
    ERROR = "error"
    TESTING = "testing"


class CRMProvider(Enum):
    """CRM providers"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    CUSTOM = "custom"


class ERPProvider(Enum):
    """ERP providers"""
    SAP = "sap"
    ORACLE = "oracle"
    NETSUITE = "netsuite"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    CUSTOM = "custom"


class PaymentProvider(Enum):
    """Payment providers"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    SQUARE = "square"
    ADYEN = "adyen"
    CUSTOM = "custom"


class SyncDirection(Enum):
    """Data sync direction"""
    BIDIRECTIONAL = "bidirectional"
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class DataType(Enum):
    """Data types for integration"""
    CONTACTS = "contacts"
    LEADS = "leads"
    OPPORTUNITIES = "opportunities"
    ACCOUNTS = "accounts"
    ORDERS = "orders"
    INVOICES = "invoices"
    PAYMENTS = "payments"
    CUSTOM = "custom"


@dataclass
class IntegrationConfig:
    """Integration configuration"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    sync_frequency_minutes: int = 30
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    data_types: List[DataType] = field(default_factory=list)
    retry_attempts: int = 3
    timeout_seconds: int = 30


@dataclass
class IntegrationCredential:
    """Integration credentials"""
    credential_id: str
    integration_id: str
    provider: str
    credentials: Dict[str, Any]
    encrypted: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class SyncJob:
    """Data synchronization job"""
    job_id: str
    integration_id: str
    data_type: DataType
    direction: SyncDirection
    status: str = "pending"
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketplaceApp:
    """Marketplace application"""
    app_id: str
    name: str
    description: str
    provider: str
    version: str
    category: str
    pricing_model: str
    api_endpoints: List[str] = field(default_factory=list)
    webhook_events: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    support_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Integration:
    """Integration information"""
    integration_id: str
    name: str
    type: IntegrationType
    provider: str
    status: IntegrationStatus
    config: IntegrationConfig
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


class IntegrationManager:
    """
    Integration capabilities manager
    
    Provides CRM integrations, ERP system integration, payment gateway
    integration, and third-party API marketplace capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the integration manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Integration storage
        self.integrations: Dict[str, Integration] = {}
        self.credentials: Dict[str, IntegrationCredential] = {}
        self.sync_jobs: List[SyncJob] = []
        self.marketplace_apps: Dict[str, MarketplaceApp] = {}
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Background tasks
        self._sync_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Integration handlers
        self._crm_handlers: Dict[str, Callable] = {}
        self._erp_handlers: Dict[str, Callable] = {}
        self._payment_handlers: Dict[str, Callable] = {}
        
        self.logger.info("IntegrationManager initialized")
    
    async def start(self):
        """Start the integration manager"""
        self.session = aiohttp.ClientSession()
        self._sync_task = asyncio.create_task(self._sync_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self.logger.info("IntegrationManager started")
    
    async def stop(self):
        """Stop the integration manager"""
        if self._sync_task:
            self._sync_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
        if self.session:
            await self.session.close()
        self.logger.info("IntegrationManager stopped")
    
    # Integration Management
    
    async def create_integration(
        self,
        name: str,
        type: IntegrationType,
        provider: str,
        tenant_id: str,
        config: IntegrationConfig
    ) -> Integration:
        """
        Create a new integration.
        
        Args:
            name: Integration name
            type: Integration type
            provider: Provider name
            tenant_id: Tenant ID
            config: Integration configuration
            
        Returns:
            Created integration
        """
        integration_id = str(uuid.uuid4())
        
        integration = Integration(
            integration_id=integration_id,
            name=name,
            type=type,
            provider=provider,
            status=IntegrationStatus.CONFIGURING,
            config=config,
            tenant_id=tenant_id
        )
        
        self.integrations[integration_id] = integration
        
        self.logger.info(f"Created integration {name} ({integration_id}) for tenant {tenant_id}")
        return integration
    
    async def update_integration(
        self,
        integration_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Integration]:
        """
        Update integration information.
        
        Args:
            integration_id: Integration ID
            updates: Update dictionary
            
        Returns:
            Updated integration or None if not found
        """
        if integration_id not in self.integrations:
            return None
        
        integration = self.integrations[integration_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(integration, key):
                setattr(integration, key, value)
        
        integration.updated_at = datetime.utcnow()
        
        self.logger.info(f"Updated integration {integration_id}")
        return integration
    
    async def get_integration(self, integration_id: str) -> Optional[Integration]:
        """Get integration by ID"""
        return self.integrations.get(integration_id)
    
    async def list_integrations(
        self,
        tenant_id: str,
        type: Optional[IntegrationType] = None,
        status: Optional[IntegrationStatus] = None
    ) -> List[Integration]:
        """List integrations with optional filtering"""
        integrations = [i for i in self.integrations.values() if i.tenant_id == tenant_id]
        
        if type:
            integrations = [i for i in integrations if i.type == type]
        
        if status:
            integrations = [i for i in integrations if i.status == status]
        
        return integrations
    
    async def delete_integration(self, integration_id: str) -> bool:
        """
        Delete an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            True if successful
        """
        if integration_id not in self.integrations:
            return False
        
        # Clean up related data
        credentials_to_delete = [
            cred_id for cred_id, cred in self.credentials.items()
            if cred.integration_id == integration_id
        ]
        
        for cred_id in credentials_to_delete:
            del self.credentials[cred_id]
        
        del self.integrations[integration_id]
        
        self.logger.info(f"Deleted integration {integration_id}")
        return True
    
    # Credential Management
    
    async def store_credentials(
        self,
        integration_id: str,
        provider: str,
        credentials: Dict[str, Any],
        encrypted: bool = True
    ) -> IntegrationCredential:
        """
        Store integration credentials.
        
        Args:
            integration_id: Integration ID
            provider: Provider name
            credentials: Credential data
            encrypted: Whether credentials are encrypted
            
        Returns:
            Stored credential
        """
        credential_id = str(uuid.uuid4())
        
        credential = IntegrationCredential(
            credential_id=credential_id,
            integration_id=integration_id,
            provider=provider,
            credentials=credentials,
            encrypted=encrypted
        )
        
        self.credentials[credential_id] = credential
        
        self.logger.info(f"Stored credentials for integration {integration_id}")
        return credential
    
    async def get_credentials(self, integration_id: str) -> Optional[IntegrationCredential]:
        """Get credentials for an integration"""
        for credential in self.credentials.values():
            if credential.integration_id == integration_id:
                return credential
        return None
    
    async def update_credentials(
        self,
        credential_id: str,
        credentials: Dict[str, Any]
    ) -> Optional[IntegrationCredential]:
        """
        Update integration credentials.
        
        Args:
            credential_id: Credential ID
            credentials: New credential data
            
        Returns:
            Updated credential or None if not found
        """
        if credential_id not in self.credentials:
            return None
        
        credential = self.credentials[credential_id]
        credential.credentials = credentials
        credential.updated_at = datetime.utcnow()
        
        self.logger.info(f"Updated credentials {credential_id}")
        return credential
    
    async def delete_credentials(self, credential_id: str) -> bool:
        """
        Delete integration credentials.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            True if successful
        """
        if credential_id not in self.credentials:
            return False
        
        del self.credentials[credential_id]
        
        self.logger.info(f"Deleted credentials {credential_id}")
        return True
    
    # CRM Integration
    
    async def create_crm_integration(
        self,
        name: str,
        provider: CRMProvider,
        tenant_id: str,
        config: IntegrationConfig
    ) -> Integration:
        """
        Create a CRM integration.
        
        Args:
            name: Integration name
            provider: CRM provider
            tenant_id: Tenant ID
            config: Integration configuration
            
        Returns:
            Created integration
        """
        return await self.create_integration(
            name=name,
            type=IntegrationType.CRM,
            provider=provider.value,
            tenant_id=tenant_id,
            config=config
        )
    
    async def sync_crm_data(
        self,
        integration_id: str,
        data_type: DataType,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> SyncJob:
        """
        Synchronize CRM data.
        
        Args:
            integration_id: Integration ID
            data_type: Type of data to sync
            direction: Sync direction
            
        Returns:
            Sync job
        """
        integration = self.integrations.get(integration_id)
        if not integration or integration.type != IntegrationType.CRM:
            raise ValueError("Invalid CRM integration")
        
        job = SyncJob(
            job_id=str(uuid.uuid4()),
            integration_id=integration_id,
            data_type=data_type,
            direction=direction,
            started_at=datetime.utcnow()
        )
        
        self.sync_jobs.append(job)
        
        # Start sync process
        asyncio.create_task(self._execute_crm_sync(job))
        
        self.logger.info(f"Started CRM sync job {job.job_id} for {data_type.value}")
        return job
    
    async def _execute_crm_sync(self, job: SyncJob):
        """Execute CRM data synchronization"""
        try:
            integration = self.integrations[job.integration_id]
            credential = await self.get_credentials(job.integration_id)
            
            if not credential:
                job.status = "failed"
                job.error_message = "No credentials found"
                job.completed_at = datetime.utcnow()
                return
            
            # Get appropriate handler
            handler = self._crm_handlers.get(integration.provider)
            if not handler:
                job.status = "failed"
                job.error_message = f"No handler for provider {integration.provider}"
                job.completed_at = datetime.utcnow()
                return
            
            # Execute sync
            result = await handler(job, integration, credential)
            
            job.records_processed = result.get('processed', 0)
            job.records_successful = result.get('successful', 0)
            job.records_failed = result.get('failed', 0)
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            # Update integration
            integration.last_sync_at = datetime.utcnow()
            integration.error_count = 0
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            # Update integration error count
            integration = self.integrations.get(job.integration_id)
            if integration:
                integration.error_count += 1
                integration.last_error = str(e)
            
            self.logger.error(f"CRM sync failed for job {job.job_id}: {e}")
    
    # ERP Integration
    
    async def create_erp_integration(
        self,
        name: str,
        provider: ERPProvider,
        tenant_id: str,
        config: IntegrationConfig
    ) -> Integration:
        """
        Create an ERP integration.
        
        Args:
            name: Integration name
            provider: ERP provider
            tenant_id: Tenant ID
            config: Integration configuration
            
        Returns:
            Created integration
        """
        return await self.create_integration(
            name=name,
            type=IntegrationType.ERP,
            provider=provider.value,
            tenant_id=tenant_id,
            config=config
        )
    
    async def sync_erp_data(
        self,
        integration_id: str,
        data_type: DataType,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> SyncJob:
        """
        Synchronize ERP data.
        
        Args:
            integration_id: Integration ID
            data_type: Type of data to sync
            direction: Sync direction
            
        Returns:
            Sync job
        """
        integration = self.integrations.get(integration_id)
        if not integration or integration.type != IntegrationType.ERP:
            raise ValueError("Invalid ERP integration")
        
        job = SyncJob(
            job_id=str(uuid.uuid4()),
            integration_id=integration_id,
            data_type=data_type,
            direction=direction,
            started_at=datetime.utcnow()
        )
        
        self.sync_jobs.append(job)
        
        # Start sync process
        asyncio.create_task(self._execute_erp_sync(job))
        
        self.logger.info(f"Started ERP sync job {job.job_id} for {data_type.value}")
        return job
    
    async def _execute_erp_sync(self, job: SyncJob):
        """Execute ERP data synchronization"""
        try:
            integration = self.integrations[job.integration_id]
            credential = await self.get_credentials(job.integration_id)
            
            if not credential:
                job.status = "failed"
                job.error_message = "No credentials found"
                job.completed_at = datetime.utcnow()
                return
            
            # Get appropriate handler
            handler = self._erp_handlers.get(integration.provider)
            if not handler:
                job.status = "failed"
                job.error_message = f"No handler for provider {integration.provider}"
                job.completed_at = datetime.utcnow()
                return
            
            # Execute sync
            result = await handler(job, integration, credential)
            
            job.records_processed = result.get('processed', 0)
            job.records_successful = result.get('successful', 0)
            job.records_failed = result.get('failed', 0)
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            # Update integration
            integration.last_sync_at = datetime.utcnow()
            integration.error_count = 0
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            # Update integration error count
            integration = self.integrations.get(job.integration_id)
            if integration:
                integration.error_count += 1
                integration.last_error = str(e)
            
            self.logger.error(f"ERP sync failed for job {job.job_id}: {e}")
    
    # Payment Gateway Integration
    
    async def create_payment_integration(
        self,
        name: str,
        provider: PaymentProvider,
        tenant_id: str,
        config: IntegrationConfig
    ) -> Integration:
        """
        Create a payment gateway integration.
        
        Args:
            name: Integration name
            provider: Payment provider
            tenant_id: Tenant ID
            config: Integration configuration
            
        Returns:
            Created integration
        """
        return await self.create_integration(
            name=name,
            type=IntegrationType.PAYMENT,
            provider=provider.value,
            tenant_id=tenant_id,
            config=config
        )
    
    async def process_payment(
        self,
        integration_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a payment through the integration.
        
        Args:
            integration_id: Integration ID
            amount: Payment amount
            currency: Currency code
            payment_method: Payment method
            metadata: Additional metadata
            
        Returns:
            Payment result
        """
        integration = self.integrations.get(integration_id)
        if not integration or integration.type != IntegrationType.PAYMENT:
            raise ValueError("Invalid payment integration")
        
        credential = await self.get_credentials(integration_id)
        if not credential:
            raise ValueError("No credentials found for payment integration")
        
        # Get appropriate handler
        handler = self._payment_handlers.get(integration.provider)
        if not handler:
            raise ValueError(f"No handler for payment provider {integration.provider}")
        
        # Process payment
        result = await handler(amount, currency, payment_method, metadata, integration, credential)
        
        self.logger.info(f"Processed payment through {integration.provider}: {result.get('transaction_id', 'unknown')}")
        return result
    
    # Marketplace Management
    
    async def register_marketplace_app(
        self,
        name: str,
        description: str,
        provider: str,
        version: str,
        category: str,
        pricing_model: str,
        api_endpoints: Optional[List[str]] = None,
        webhook_events: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
        support_url: Optional[str] = None
    ) -> MarketplaceApp:
        """
        Register a marketplace application.
        
        Args:
            name: App name
            description: App description
            provider: Provider name
            version: App version
            category: App category
            pricing_model: Pricing model
            api_endpoints: Available API endpoints
            webhook_events: Supported webhook events
            documentation_url: Documentation URL
            support_url: Support URL
            
        Returns:
            Registered app
        """
        app_id = str(uuid.uuid4())
        
        app = MarketplaceApp(
            app_id=app_id,
            name=name,
            description=description,
            provider=provider,
            version=version,
            category=category,
            pricing_model=pricing_model,
            api_endpoints=api_endpoints or [],
            webhook_events=webhook_events or [],
            documentation_url=documentation_url,
            support_url=support_url
        )
        
        self.marketplace_apps[app_id] = app
        
        self.logger.info(f"Registered marketplace app {name} ({app_id})")
        return app
    
    async def get_marketplace_app(self, app_id: str) -> Optional[MarketplaceApp]:
        """Get marketplace app by ID"""
        return self.marketplace_apps.get(app_id)
    
    async def list_marketplace_apps(
        self,
        category: Optional[str] = None,
        provider: Optional[str] = None,
        active_only: bool = True
    ) -> List[MarketplaceApp]:
        """List marketplace apps with optional filtering"""
        apps = list(self.marketplace_apps.values())
        
        if category:
            apps = [app for app in apps if app.category == category]
        
        if provider:
            apps = [app for app in apps if app.provider == provider]
        
        if active_only:
            apps = [app for app in apps if app.is_active]
        
        return apps
    
    async def update_marketplace_app(
        self,
        app_id: str,
        updates: Dict[str, Any]
    ) -> Optional[MarketplaceApp]:
        """
        Update marketplace app information.
        
        Args:
            app_id: App ID
            updates: Update dictionary
            
        Returns:
            Updated app or None if not found
        """
        if app_id not in self.marketplace_apps:
            return None
        
        app = self.marketplace_apps[app_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(app, key):
                setattr(app, key, value)
        
        app.updated_at = datetime.utcnow()
        
        self.logger.info(f"Updated marketplace app {app_id}")
        return app
    
    # Sync Job Management
    
    async def get_sync_jobs(
        self,
        integration_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SyncJob]:
        """Get sync jobs with optional filtering"""
        jobs = list(self.sync_jobs)
        
        if integration_id:
            jobs = [job for job in jobs if job.integration_id == integration_id]
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return jobs[offset:offset + limit]
    
    async def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID"""
        for job in self.sync_jobs:
            if job.job_id == job_id:
                return job
        return None
    
    # Integration Handlers
    
    def register_crm_handler(self, provider: str, handler: Callable):
        """Register a CRM integration handler"""
        self._crm_handlers[provider] = handler
        self.logger.info(f"Registered CRM handler for {provider}")
    
    def register_erp_handler(self, provider: str, handler: Callable):
        """Register an ERP integration handler"""
        self._erp_handlers[provider] = handler
        self.logger.info(f"Registered ERP handler for {provider}")
    
    def register_payment_handler(self, provider: str, handler: Callable):
        """Register a payment integration handler"""
        self._payment_handlers[provider] = handler
        self.logger.info(f"Registered payment handler for {provider}")
    
    # Background Tasks
    
    async def _sync_loop(self):
        """Background task to run scheduled syncs"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.utcnow()
                
                for integration in self.integrations.values():
                    if integration.status != IntegrationStatus.ACTIVE:
                        continue
                    
                    # Check if sync is due
                    if (integration.last_sync_at is None or
                        current_time - integration.last_sync_at > timedelta(minutes=integration.config.sync_frequency_minutes)):
                        
                        # Start sync for each data type
                        for data_type in integration.config.data_types:
                            await self.sync_crm_data(
                                integration.integration_id,
                                data_type,
                                integration.config.sync_direction
                            )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
    
    async def _health_check_loop(self):
        """Background task to check integration health"""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                
                for integration in self.integrations.values():
                    if integration.status == IntegrationStatus.ACTIVE:
                        # Check error count
                        if integration.error_count > 5:
                            integration.status = IntegrationStatus.ERROR
                            self.logger.warning(f"Integration {integration.integration_id} marked as error due to high error count")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
    
    # Statistics & Monitoring
    
    async def get_integration_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get integration statistics for a tenant"""
        tenant_integrations = [i for i in self.integrations.values() if i.tenant_id == tenant_id]
        
        stats = {
            "total_integrations": len(tenant_integrations),
            "active_integrations": len([i for i in tenant_integrations if i.status == IntegrationStatus.ACTIVE]),
            "error_integrations": len([i for i in tenant_integrations if i.status == IntegrationStatus.ERROR]),
            "by_type": {},
            "by_provider": {},
            "recent_syncs": 0,
            "failed_syncs": 0
        }
        
        # Count by type
        for integration in tenant_integrations:
            type_name = integration.type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
        
        # Count by provider
        for integration in tenant_integrations:
            provider = integration.provider
            stats["by_provider"][provider] = stats["by_provider"].get(provider, 0) + 1
        
        # Count recent syncs
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        for integration in tenant_integrations:
            if integration.last_sync_at and integration.last_sync_at > one_hour_ago:
                stats["recent_syncs"] += 1
        
        # Count failed syncs
        for job in self.sync_jobs:
            if job.integration_id in [i.integration_id for i in tenant_integrations] and job.status == "failed":
                stats["failed_syncs"] += 1
        
        return stats
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide integration statistics"""
        return {
            "total_integrations": len(self.integrations),
            "total_credentials": len(self.credentials),
            "total_sync_jobs": len(self.sync_jobs),
            "total_marketplace_apps": len(self.marketplace_apps),
            "active_integrations": len([i for i in self.integrations.values() if i.status == IntegrationStatus.ACTIVE]),
            "error_integrations": len([i for i in self.integrations.values() if i.status == IntegrationStatus.ERROR]),
            "pending_sync_jobs": len([j for j in self.sync_jobs if j.status == "pending"]),
            "failed_sync_jobs": len([j for j in self.sync_jobs if j.status == "failed"])
        }
