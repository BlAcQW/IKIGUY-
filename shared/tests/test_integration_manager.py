"""
Tests for Integration Capabilities

This module tests the integration capabilities including:
- CRM integrations (Salesforce, HubSpot)
- ERP system integration
- Payment gateway integration
- Third-party API marketplace
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from apps.shared.integration.integration_manager import (
    IntegrationManager,
    IntegrationType,
    IntegrationStatus,
    CRMProvider,
    ERPProvider,
    PaymentProvider,
    SyncDirection,
    DataType,
    IntegrationConfig,
    IntegrationCredential,
    SyncJob,
    MarketplaceApp,
    Integration
)


class TestIntegrationManager:
    """Test cases for IntegrationManager"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'sync_interval_minutes': 30,
            'health_check_interval_minutes': 10,
            'max_retry_attempts': 3,
            'timeout_seconds': 30
        }

    @pytest.fixture
    def integration_manager(self, config):
        """Fixture for IntegrationManager instance"""
        with patch('shared.integration.integration_manager.logging.getLogger'):
            return IntegrationManager(config)

    @pytest.fixture
    def sample_config(self):
        """Sample integration configuration"""
        return IntegrationConfig(
            api_key="test_api_key",
            api_secret="test_api_secret",
            base_url="https://api.example.com",
            webhook_url="https://webhook.example.com",
            sync_frequency_minutes=30,
            sync_direction=SyncDirection.BIDIRECTIONAL,
            data_types=[DataType.CONTACTS, DataType.LEADS],
            retry_attempts=3,
            timeout_seconds=30
        )

    @pytest.fixture
    def sample_credentials(self):
        """Sample integration credentials"""
        return {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret",
            "access_token": "test_access_token"
        }

    # Integration Management Tests

    @pytest.mark.asyncio
    async def test_create_integration_success(self, integration_manager, sample_config):
        """Test successful integration creation"""
        integration = await integration_manager.create_integration(
            name="Test CRM Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        assert integration is not None
        assert integration.name == "Test CRM Integration"
        assert integration.type == IntegrationType.CRM
        assert integration.provider == "salesforce"
        assert integration.status == IntegrationStatus.CONFIGURING
        assert integration.tenant_id == "test-tenant"
        assert integration.config == sample_config
        assert integration.integration_id in integration_manager.integrations

    @pytest.mark.asyncio
    async def test_update_integration_success(self, integration_manager, sample_config):
        """Test successful integration update"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        updates = {
            'name': 'Updated Integration',
            'status': IntegrationStatus.ACTIVE
        }
        
        updated_integration = await integration_manager.update_integration(
            integration.integration_id, updates
        )
        
        assert updated_integration is not None
        assert updated_integration.name == 'Updated Integration'
        assert updated_integration.status == IntegrationStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_integration_not_found(self, integration_manager):
        """Test integration update with non-existent integration"""
        result = await integration_manager.update_integration(
            'non-existent-id', {'name': 'Test'}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_integration_success(self, integration_manager, sample_config):
        """Test getting integration by ID"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        retrieved_integration = await integration_manager.get_integration(integration.integration_id)
        assert retrieved_integration == integration

    @pytest.mark.asyncio
    async def test_get_integration_not_found(self, integration_manager):
        """Test getting non-existent integration"""
        result = await integration_manager.get_integration('non-existent-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_list_integrations(self, integration_manager, sample_config):
        """Test listing integrations"""
        # Create multiple integrations
        integration1 = await integration_manager.create_integration(
            name="CRM Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        integration2 = await integration_manager.create_integration(
            name="ERP Integration",
            type=IntegrationType.ERP,
            provider="sap",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        # List all integrations
        all_integrations = await integration_manager.list_integrations("test-tenant")
        assert len(all_integrations) == 2
        
        # List by type
        crm_integrations = await integration_manager.list_integrations(
            "test-tenant", type=IntegrationType.CRM
        )
        assert len(crm_integrations) == 1
        assert crm_integrations[0].type == IntegrationType.CRM

    @pytest.mark.asyncio
    async def test_delete_integration_success(self, integration_manager, sample_config):
        """Test successful integration deletion"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        # Store credentials
        await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            {"api_key": "test"}
        )
        
        # Delete integration
        result = await integration_manager.delete_integration(integration.integration_id)
        assert result is True
        assert integration.integration_id not in integration_manager.integrations
        
        # Check that credentials were also deleted
        credential = await integration_manager.get_credentials(integration.integration_id)
        assert credential is None

    @pytest.mark.asyncio
    async def test_delete_integration_not_found(self, integration_manager):
        """Test integration deletion with non-existent integration"""
        result = await integration_manager.delete_integration('non-existent-id')
        assert result is False

    # Credential Management Tests

    @pytest.mark.asyncio
    async def test_store_credentials_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful credential storage"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        credential = await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        assert credential is not None
        assert credential.integration_id == integration.integration_id
        assert credential.provider == "salesforce"
        assert credential.credentials == sample_credentials
        assert credential.credential_id in integration_manager.credentials

    @pytest.mark.asyncio
    async def test_get_credentials_success(self, integration_manager, sample_config, sample_credentials):
        """Test getting credentials"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        stored_credential = await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        retrieved_credential = await integration_manager.get_credentials(integration.integration_id)
        assert retrieved_credential == stored_credential

    @pytest.mark.asyncio
    async def test_get_credentials_not_found(self, integration_manager):
        """Test getting credentials for non-existent integration"""
        result = await integration_manager.get_credentials('non-existent-id')
        assert result is None

    @pytest.mark.asyncio
    async def test_update_credentials_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful credential update"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        credential = await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        new_credentials = {"api_key": "new_key", "api_secret": "new_secret"}
        updated_credential = await integration_manager.update_credentials(
            credential.credential_id, new_credentials
        )
        
        assert updated_credential is not None
        assert updated_credential.credentials == new_credentials

    @pytest.mark.asyncio
    async def test_delete_credentials_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful credential deletion"""
        integration = await integration_manager.create_integration(
            name="Test Integration",
            type=IntegrationType.CRM,
            provider="salesforce",
            tenant_id="test-tenant",
            config=sample_config
        )
        
        credential = await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        result = await integration_manager.delete_credentials(credential.credential_id)
        assert result is True
        assert credential.credential_id not in integration_manager.credentials

    # CRM Integration Tests

    @pytest.mark.asyncio
    async def test_create_crm_integration_success(self, integration_manager, sample_config):
        """Test successful CRM integration creation"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        assert integration is not None
        assert integration.type == IntegrationType.CRM
        assert integration.provider == CRMProvider.SALESFORCE.value

    @pytest.mark.asyncio
    async def test_sync_crm_data_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful CRM data synchronization"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        # Register a mock handler
        async def mock_crm_handler(job, integration, credential):
            return {'processed': 10, 'successful': 8, 'failed': 2}
        
        integration_manager.register_crm_handler("salesforce", mock_crm_handler)
        
        job = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.CONTACTS,
            SyncDirection.BIDIRECTIONAL
        )
        
        assert job is not None
        assert job.integration_id == integration.integration_id
        assert job.data_type == DataType.CONTACTS
        assert job.direction == SyncDirection.BIDIRECTIONAL
        
        # Wait for sync to complete
        await asyncio.sleep(0.1)
        
        # Check job status
        updated_job = await integration_manager.get_sync_job(job.job_id)
        assert updated_job is not None
        assert updated_job.status == "completed"

    @pytest.mark.asyncio
    async def test_sync_crm_data_invalid_integration(self, integration_manager):
        """Test CRM sync with invalid integration"""
        with pytest.raises(ValueError, match="Invalid CRM integration"):
            await integration_manager.sync_crm_data(
                "non-existent-id",
                DataType.CONTACTS
            )

    # ERP Integration Tests

    @pytest.mark.asyncio
    async def test_create_erp_integration_success(self, integration_manager, sample_config):
        """Test successful ERP integration creation"""
        integration = await integration_manager.create_erp_integration(
            name="SAP Integration",
            provider=ERPProvider.SAP,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        assert integration is not None
        assert integration.type == IntegrationType.ERP
        assert integration.provider == ERPProvider.SAP.value

    @pytest.mark.asyncio
    async def test_sync_erp_data_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful ERP data synchronization"""
        integration = await integration_manager.create_erp_integration(
            name="SAP Integration",
            provider=ERPProvider.SAP,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "sap",
            sample_credentials
        )
        
        # Register a mock handler
        async def mock_erp_handler(job, integration, credential):
            return {'processed': 15, 'successful': 12, 'failed': 3}
        
        integration_manager.register_erp_handler("sap", mock_erp_handler)
        
        job = await integration_manager.sync_erp_data(
            integration.integration_id,
            DataType.ORDERS,
            SyncDirection.INBOUND
        )
        
        assert job is not None
        assert job.integration_id == integration.integration_id
        assert job.data_type == DataType.ORDERS
        assert job.direction == SyncDirection.INBOUND

    # Payment Gateway Integration Tests

    @pytest.mark.asyncio
    async def test_create_payment_integration_success(self, integration_manager, sample_config):
        """Test successful payment integration creation"""
        integration = await integration_manager.create_payment_integration(
            name="Stripe Integration",
            provider=PaymentProvider.STRIPE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        assert integration is not None
        assert integration.type == IntegrationType.PAYMENT
        assert integration.provider == PaymentProvider.STRIPE.value

    @pytest.mark.asyncio
    async def test_process_payment_success(self, integration_manager, sample_config, sample_credentials):
        """Test successful payment processing"""
        integration = await integration_manager.create_payment_integration(
            name="Stripe Integration",
            provider=PaymentProvider.STRIPE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "stripe",
            sample_credentials
        )
        
        # Register a mock handler
        async def mock_payment_handler(amount, currency, payment_method, metadata, integration, credential):
            return {
                'transaction_id': 'txn_123456',
                'status': 'succeeded',
                'amount': amount,
                'currency': currency
            }
        
        integration_manager.register_payment_handler("stripe", mock_payment_handler)
        
        result = await integration_manager.process_payment(
            integration.integration_id,
            amount=100.00,
            currency="USD",
            payment_method="card",
            metadata={"order_id": "order_123"}
        )
        
        assert result is not None
        assert result['transaction_id'] == 'txn_123456'
        assert result['status'] == 'succeeded'
        assert result['amount'] == 100.00

    @pytest.mark.asyncio
    async def test_process_payment_invalid_integration(self, integration_manager):
        """Test payment processing with invalid integration"""
        with pytest.raises(ValueError, match="Invalid payment integration"):
            await integration_manager.process_payment(
                "non-existent-id",
                amount=100.00,
                currency="USD",
                payment_method="card"
            )

    # Marketplace Management Tests

    @pytest.mark.asyncio
    async def test_register_marketplace_app_success(self, integration_manager):
        """Test successful marketplace app registration"""
        app = await integration_manager.register_marketplace_app(
            name="Test App",
            description="A test marketplace app",
            provider="Test Provider",
            version="1.0.0",
            category="CRM",
            pricing_model="subscription",
            api_endpoints=["/api/v1/contacts", "/api/v1/leads"],
            webhook_events=["contact.created", "lead.updated"],
            documentation_url="https://docs.example.com",
            support_url="https://support.example.com"
        )
        
        assert app is not None
        assert app.name == "Test App"
        assert app.description == "A test marketplace app"
        assert app.provider == "Test Provider"
        assert app.version == "1.0.0"
        assert app.category == "CRM"
        assert app.pricing_model == "subscription"
        assert len(app.api_endpoints) == 2
        assert len(app.webhook_events) == 2
        assert app.app_id in integration_manager.marketplace_apps

    @pytest.mark.asyncio
    async def test_get_marketplace_app_success(self, integration_manager):
        """Test getting marketplace app by ID"""
        app = await integration_manager.register_marketplace_app(
            name="Test App",
            description="A test marketplace app",
            provider="Test Provider",
            version="1.0.0",
            category="CRM",
            pricing_model="subscription"
        )
        
        retrieved_app = await integration_manager.get_marketplace_app(app.app_id)
        assert retrieved_app == app

    @pytest.mark.asyncio
    async def test_list_marketplace_apps(self, integration_manager):
        """Test listing marketplace apps"""
        # Create multiple apps
        app1 = await integration_manager.register_marketplace_app(
            name="CRM App",
            description="CRM integration app",
            provider="Provider A",
            version="1.0.0",
            category="CRM",
            pricing_model="subscription"
        )
        app2 = await integration_manager.register_marketplace_app(
            name="ERP App",
            description="ERP integration app",
            provider="Provider B",
            version="2.0.0",
            category="ERP",
            pricing_model="one-time"
        )
        
        # List all apps
        all_apps = await integration_manager.list_marketplace_apps()
        assert len(all_apps) == 2
        
        # List by category
        crm_apps = await integration_manager.list_marketplace_apps(category="CRM")
        assert len(crm_apps) == 1
        assert crm_apps[0].category == "CRM"
        
        # List by provider
        provider_a_apps = await integration_manager.list_marketplace_apps(provider="Provider A")
        assert len(provider_a_apps) == 1
        assert provider_a_apps[0].provider == "Provider A"

    @pytest.mark.asyncio
    async def test_update_marketplace_app_success(self, integration_manager):
        """Test successful marketplace app update"""
        app = await integration_manager.register_marketplace_app(
            name="Test App",
            description="A test marketplace app",
            provider="Test Provider",
            version="1.0.0",
            category="CRM",
            pricing_model="subscription"
        )
        
        updates = {
            'name': 'Updated App',
            'version': '2.0.0',
            'is_active': False
        }
        
        updated_app = await integration_manager.update_marketplace_app(app.app_id, updates)
        
        assert updated_app is not None
        assert updated_app.name == 'Updated App'
        assert updated_app.version == '2.0.0'
        assert updated_app.is_active is False

    # Sync Job Management Tests

    @pytest.mark.asyncio
    async def test_get_sync_jobs(self, integration_manager, sample_config, sample_credentials):
        """Test getting sync jobs"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        # Register a mock handler
        async def mock_handler(job, integration, credential):
            return {'processed': 5, 'successful': 5, 'failed': 0}
        
        integration_manager.register_crm_handler("salesforce", mock_handler)
        
        # Create sync jobs
        job1 = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.CONTACTS
        )
        job2 = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.LEADS
        )
        
        # Wait for jobs to complete
        await asyncio.sleep(0.1)
        
        # Get all jobs
        all_jobs = await integration_manager.get_sync_jobs()
        assert len(all_jobs) >= 2
        
        # Get jobs by integration
        integration_jobs = await integration_manager.get_sync_jobs(
            integration_id=integration.integration_id
        )
        assert len(integration_jobs) >= 2
        
        # Get completed jobs
        completed_jobs = await integration_manager.get_sync_jobs(status="completed")
        assert len(completed_jobs) >= 2

    @pytest.mark.asyncio
    async def test_get_sync_job_success(self, integration_manager, sample_config, sample_credentials):
        """Test getting sync job by ID"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        # Register a mock handler
        async def mock_handler(job, integration, credential):
            return {'processed': 5, 'successful': 5, 'failed': 0}
        
        integration_manager.register_crm_handler("salesforce", mock_handler)
        
        job = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.CONTACTS
        )
        
        # Wait for job to complete
        await asyncio.sleep(0.1)
        
        retrieved_job = await integration_manager.get_sync_job(job.job_id)
        assert retrieved_job is not None
        assert retrieved_job.job_id == job.job_id

    # Integration Handler Registration Tests

    @pytest.mark.asyncio
    async def test_register_crm_handler(self, integration_manager):
        """Test CRM handler registration"""
        async def test_handler(job, integration, credential):
            return {'processed': 1, 'successful': 1, 'failed': 0}
        
        integration_manager.register_crm_handler("salesforce", test_handler)
        assert "salesforce" in integration_manager._crm_handlers

    @pytest.mark.asyncio
    async def test_register_erp_handler(self, integration_manager):
        """Test ERP handler registration"""
        async def test_handler(job, integration, credential):
            return {'processed': 1, 'successful': 1, 'failed': 0}
        
        integration_manager.register_erp_handler("sap", test_handler)
        assert "sap" in integration_manager._erp_handlers

    @pytest.mark.asyncio
    async def test_register_payment_handler(self, integration_manager):
        """Test payment handler registration"""
        async def test_handler(amount, currency, payment_method, metadata, integration, credential):
            return {'transaction_id': 'test', 'status': 'succeeded'}
        
        integration_manager.register_payment_handler("stripe", test_handler)
        assert "stripe" in integration_manager._payment_handlers

    # Background Tasks Tests

    @pytest.mark.asyncio
    async def test_start_and_stop(self, integration_manager):
        """Test starting and stopping the manager"""
        await integration_manager.start()
        assert integration_manager.session is not None
        assert integration_manager._sync_task is not None
        assert integration_manager._health_check_task is not None
        
        await integration_manager.stop()
        # Tasks should be cancelled
        await asyncio.sleep(0.1)  # Give time for cancellation to process
        assert integration_manager._sync_task.done() is True
        assert integration_manager._health_check_task.done() is True

    # Statistics & Monitoring Tests

    @pytest.mark.asyncio
    async def test_get_integration_statistics(self, integration_manager, sample_config):
        """Test integration statistics generation"""
        # Create integrations
        crm_integration = await integration_manager.create_crm_integration(
            name="CRM Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        erp_integration = await integration_manager.create_erp_integration(
            name="ERP Integration",
            provider=ERPProvider.SAP,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        # Activate integrations
        await integration_manager.update_integration(
            crm_integration.integration_id, {'status': IntegrationStatus.ACTIVE}
        )
        await integration_manager.update_integration(
            erp_integration.integration_id, {'status': IntegrationStatus.ERROR}
        )
        
        stats = await integration_manager.get_integration_statistics("test-tenant")
        
        assert stats['total_integrations'] == 2
        assert stats['active_integrations'] == 1
        assert stats['error_integrations'] == 1
        assert 'by_type' in stats
        assert 'by_provider' in stats

    @pytest.mark.asyncio
    async def test_get_system_statistics(self, integration_manager, sample_config):
        """Test system-wide statistics"""
        # Create integrations and apps
        await integration_manager.create_crm_integration(
            name="CRM Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.register_marketplace_app(
            name="Test App",
            description="Test app",
            provider="Test Provider",
            version="1.0.0",
            category="CRM",
            pricing_model="subscription"
        )
        
        stats = await integration_manager.get_system_statistics()
        
        assert stats['total_integrations'] == 1
        assert stats['total_marketplace_apps'] == 1
        assert 'active_integrations' in stats
        assert 'error_integrations' in stats
        assert 'pending_sync_jobs' in stats
        assert 'failed_sync_jobs' in stats

    # Edge Cases and Error Handling

    @pytest.mark.asyncio
    async def test_sync_without_credentials(self, integration_manager, sample_config):
        """Test sync without stored credentials"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        # Register a mock handler
        async def mock_handler(job, integration, credential):
            return {'processed': 1, 'successful': 1, 'failed': 0}
        
        integration_manager.register_crm_handler("salesforce", mock_handler)
        
        job = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.CONTACTS
        )
        
        # Wait for sync to complete
        await asyncio.sleep(0.1)
        
        # Check that job failed due to missing credentials
        updated_job = await integration_manager.get_sync_job(job.job_id)
        assert updated_job.status == "failed"
        assert "No credentials found" in updated_job.error_message

    @pytest.mark.asyncio
    async def test_sync_without_handler(self, integration_manager, sample_config, sample_credentials):
        """Test sync without registered handler"""
        integration = await integration_manager.create_crm_integration(
            name="Salesforce Integration",
            provider=CRMProvider.SALESFORCE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "salesforce",
            sample_credentials
        )
        
        job = await integration_manager.sync_crm_data(
            integration.integration_id,
            DataType.CONTACTS
        )
        
        # Wait for sync to complete
        await asyncio.sleep(0.1)
        
        # Check that job failed due to missing handler
        updated_job = await integration_manager.get_sync_job(job.job_id)
        assert updated_job.status == "failed"
        assert "No handler for provider" in updated_job.error_message

    @pytest.mark.asyncio
    async def test_payment_without_credentials(self, integration_manager, sample_config):
        """Test payment processing without stored credentials"""
        integration = await integration_manager.create_payment_integration(
            name="Stripe Integration",
            provider=PaymentProvider.STRIPE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        with pytest.raises(ValueError, match="No credentials found for payment integration"):
            await integration_manager.process_payment(
                integration.integration_id,
                amount=100.00,
                currency="USD",
                payment_method="card"
            )

    @pytest.mark.asyncio
    async def test_payment_without_handler(self, integration_manager, sample_config, sample_credentials):
        """Test payment processing without registered handler"""
        integration = await integration_manager.create_payment_integration(
            name="Stripe Integration",
            provider=PaymentProvider.STRIPE,
            tenant_id="test-tenant",
            config=sample_config
        )
        
        await integration_manager.store_credentials(
            integration.integration_id,
            "stripe",
            sample_credentials
        )
        
        with pytest.raises(ValueError, match="No handler for payment provider"):
            await integration_manager.process_payment(
                integration.integration_id,
                amount=100.00,
                currency="USD",
                payment_method="card"
            )
